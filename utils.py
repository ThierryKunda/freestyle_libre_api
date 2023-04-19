import hashlib

from sqlalchemy.orm import Session

import models.database as db_models

def add_new_user(db: Session, firstname: str, lastname: str, password: str):
    # Hashing the password for security concern (obviously)
    pw = hashlib.sha256(bytes(password, encoding='utf-8')).hexdigest()
    # Check if user already exists
    res = db.query(db_models.User).filter_by(firstname=firstname, lastname=lastname).first()
    if res:
        return False
    user = db_models.User(firstname=firstname, lastname=lastname, password=pw)
    db.add(user)
    db.commit()
    return user

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