import hashlib
from datetime import datetime as dt, timedelta as tdelta

from sqlalchemy.orm import Session

import models.database as db_models

def encode_secret(secret: str) -> str:
    return hashlib.sha256(bytes(secret, encoding='utf-8')).hexdigest()

def add_new_user(db: Session, firstname: str, lastname: str, password: str):
    # Hashing the password for security concern (obviously)
    pw = encode_secret(password)
    # Check if user already exists
    res = db.query(db_models.User).filter_by(firstname=firstname, lastname=lastname).first()
    if res:
        return False
    user = db_models.User(firstname=firstname, lastname=lastname, password=pw)
    db.add(user)
    db.commit()
    return user

def add_new_token(
        db: Session, firstname: str, lastname: str, password: str,
        user_profile_access: bool, samples_access: bool, goals_access: bool
        ) -> dict[str, str]:
    # Get the user
    pw = encode_secret(password)
    user = db.query(db_models.User).filter_by(firstname=firstname, lastname=lastname, password=pw).first()
    if not user:
        return None
    # Generate new token based on current date (timestamp)
    current_dt = str(dt.now().timestamp())
    tk_value = encode_secret(current_dt)
    tk = db_models.Auth(
        user_id=user.id, token_value=tk_value, expiration_date=dt.now() + tdelta(days=365),
        last_time_used=dt.now(),
        user_profile_access=user_profile_access,
        samples_access = samples_access,
        goals_access = goals_access
    )
    db.add(tk)
    db.commit()
    return {
        "id": tk.id,
        "value": tk.token_value,
        "expiration_date": tk.expiration_date
    }

def get_user_from_token(db: Session, token: str):
    # Checks if token already exists
    tk = db.query(db_models.Auth).filter_by(token_value=token).first()
    if tk:
        # Do nothing if tokens is expired
        if tk.expiration_date > dt.now():
            return None
        return db.query(db_models.User).filter_by(id=tk.user_id).first()
    else:
        return None
    
def get_token_rights(db: Session, token: str) -> dict[str, bool] | None:
    # Checks if token exists
    tk = db.query(db_models.Auth).filter_by(token_value=token).first()
    if tk:
        return {
            "user_profile": tk.user_profile_access,
            "goals": tk.goals_access,
            "samples": tk.samples_access,
        }
    return None