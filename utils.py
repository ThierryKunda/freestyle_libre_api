from sqlalchemy.orm import Session

import models.database as db_models

def add_new_user(db: Session, firstname: str, lastname: str):
    # Check if user already exists
    res = db.query(db_models.User).filter_by(firstname=firstname, lastname=lastname).first()
    if res:
        return False

    user = db_models.User(firstname=firstname, lastname=lastname)
    db.add(user)
    db.commit()
    return user