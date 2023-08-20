import os
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends, Security, status, APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from data_validation import validate_data_from_upload

from models import resources
from models.database import Base, User

import api, utils
import env

engine = create_engine(env.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={
    "profile": "Read information about user profile",
    "samples": "Read samples related to a user",
    "goals": "Read user goals",
    "stats": "Read user statistics"
})

def map_access_form_inputs(
        inputs: list[str] = ["not_allowed", "not_allowed", "not_allowed"],
        mappings: dict[str, bool] = {"allowed": True, "not_allowed": False},
        in_place: bool = False,
        input_prefixed: bool = False,
    ) -> list[bool]:
    # Default prefixes : profile samples goals stats
    if input_prefixed:
        res = [False, False, False, False]
        for s in inputs:
            if s.startswith("profile"):
                allowing = s.split(":")[1]
                res[0] = mappings[allowing]
            elif s.startswith("samples"):
                allowing = s.split(":")[1]
                res[1] = mappings[allowing]
            elif s.startswith("goals"):
                allowing = s.split(":")[1]
                res[2] = mappings[allowing]
            elif s.startswith("stats"):
                allowing = s.split(":")[1]
                res[3] = mappings[allowing]

        return res
    elif in_place:
        rights = ["profile", "samples", "goals", "stats"]
        res = [True if s in inputs else False for s in rights]
        return res
    return [mappings[inputs[i]] for i in range(len(inputs))]

async def get_authorized_user(security_scopes: SecurityScopes, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    utils.update_token_last_used_date(db, token)
    if security_scopes.scopes:
        authentificate_value = f'Bearer scope="{security_scopes.scope_str}"'
        rights = utils.get_token_rights(db, token)
        unauth_expection = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission to perform any action on specified resource(s)",
            headers={"WWW-Authenticate": authentificate_value}
        )
        if rights:
            for r in security_scopes.scopes:
                if not rights[r]:
                    raise unauth_expection
                    # if not r in security_scopes.scopes:
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token does not exist or is already expired",
                headers={"WWW-Authentificate": authentificate_value}
            )
    else:
        authentificate_value = 'Bearer'
    user = utils.get_user_from_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authentificate_value}
        )
    return user

samples_collection: dict[str, list[resources.BloodGlucoseSample]] = {}
stats_collection = {key: resources.Stats.from_sample_collection(samples_collection[key]) for key in samples_collection}

def check_username(username: str, user: User) -> None:
    if username != user.firstname + '_' + user.lastname:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token with username")

def lazy_load_user_data(username: str):
    if username not in samples_collection:
        user_data = api.samples_from_csv(filepath=os.path.join("users_data", f"{username}.csv"))
        if user_data:
            samples_collection[username] = user_data
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User data not found, based on username"
            )
        
def lazy_load_user_stats(username):
    if username not in stats_collection:
        if username in samples_collection:
            stats_collection[username] = resources.Stats.from_sample_collection(samples_collection[username])
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User data not found, based on username"
            )
        