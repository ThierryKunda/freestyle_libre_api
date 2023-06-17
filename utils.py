import hashlib
from datetime import datetime as dt, timedelta as tdelta

from sqlalchemy.orm import Session

import models.database as db_models
import models.resources as resources

def encode_secret(secret: str) -> str:
    return hashlib.sha256(bytes(secret, encoding='utf-8')).hexdigest()

def get_user(db: Session, username: str, password: str):
    pw = encode_secret(password)
    firstname, lastname = username.split("_")
    return db.query(db_models.User).filter_by(firstname=firstname, lastname=lastname, password=pw).first()

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
        if tk.expiration_date < dt.now():
            return None
        return db.query(db_models.User).filter_by(id=tk.user_id).first()
    else:
        return None
    
def get_token_rights(db: Session, token: str) -> dict[str, bool] | None:
    # Checks if token exists
    tk = db.query(db_models.Auth).filter_by(token_value=token).first()
    if tk:
        return {
            "profile": tk.user_profile_access,
            "goals": tk.goals_access,
            "samples": tk.samples_access,
        }
    return None    
def get_user_goals(db: Session, user: db_models.User):
    goals: list[db_models.Goal] = db.query(db_models.Goal).filter_by(user_id=user.id).all()
    return [
        resources.Goal(
            id=g.id,
            title=g.title,
            status=resources.GoalStatus.from_integer(g.status) if g.status else None,
            start_datetime=g.start_datetime,
            end_datetime=g.end_datetime,
            average_target=g.average_target,
            trend_target=resources.TrendState.from_integer(g.trend_target) if g.trend_target else None,
            stats_target=resources.Stats(
                minimum=g.minimum,
                maximum=g.maximum,
                stat_range=g.stat_range,
                mean=g.mean,
                median=g.median,
                standard_deviation=g.std_dev,
                overall_samples_size=g.overall_samples_size,
                first_quartile=g.first_quart,
                second_quartile=g.second_quart,
                third_quartile=g.second_quart
            )
        )
        for g in goals
    ]

def add_new_goal(
            db: Session, user: db_models.User,
            title: str,
            status: int,
            start_datetime: dt | None = None,
            end_datetime: dt | None = None,
            average_target: int | None = None,
            trend_target: int | None = None,
            minimum: int | None = None,
            maximum: int | None = None,
            stat_range: int | None = None,
            mean: float | None = None,
            variance: float | None = None,
            std_dev: float | None = None,
            overall_samples_size: int | None = None,
            first_quart: int | None = None,
            second_quart: int | None = None,
            third_quart: int | None = None,
            median: float | None = None
        ):
    existing_goal = db.query(db_models.Goal).filter_by(title=title).first()
    if existing_goal:
        return None
    g = db_models.Goal(
        user_id=user.id,
        *[
            title,
            status,
            start_datetime,
            end_datetime,
            average_target,
            trend_target,
            minimum,
            maximum,
            stat_range,
            mean,
            variance,
            std_dev,
            overall_samples_size,
            first_quart,
            second_quart,
            third_quart,
            median
            ]

    )
    db.add(g)
    db.commit()
    return g