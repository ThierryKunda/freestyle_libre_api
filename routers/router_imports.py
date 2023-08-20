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