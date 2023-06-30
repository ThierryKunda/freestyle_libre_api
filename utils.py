import hashlib
from typing import Literal
from datetime import datetime as dt, timedelta as tdelta

from sqlalchemy.orm import Session
from sqlalchemy import desc

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

def days_from_unit(value: int, unit: str) -> int:
    if unit == "days":
        return value
    elif unit == "months":
        return value * 30
    elif unit == "years":
        return value * 365
    else:
        raise ValueError("Invalid time unit")

def generate_token_value(db: Session, firstname: str, lastname: str) -> tuple[str, int] | None:
    last_signature = db.query(db_models.SecretSignature).order_by(
        desc(db_models.SecretSignature.generation_date)
        ).first()
    if last_signature:
        return (encode_secret(firstname[:2]+lastname[-2:]+str(dt.now())+last_signature.secret_value), last_signature.id)
    return None

def add_new_token(
        db: Session, firstname: str, lastname: str, password: str,
        user_profile_access: bool, samples_access: bool, goals_access: bool,
        expiration_value: str = "3", expiration_unit: Literal["days", "months", "years"] = "months",
        ) -> dict[str, str] | None:
    # Get the user
    pw = encode_secret(password)
    user = db.query(db_models.User).filter_by(firstname=firstname, lastname=lastname, password=pw).first()
    if not user:
        return None
    tk_value = generate_token_value(db, firstname, lastname)
    if not tk_value:
        return None
    tk = db_models.Auth(
        user_id=user.id,
        signature_used=tk_value[1],
        token_value=tk_value[0],
        expiration_date=dt.now() + tdelta(days=days_from_unit(int(expiration_value), expiration_unit)),
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
        if tk.expiration_date >= dt.now():
            return {
                "profile": tk.user_profile_access,
                "goals": tk.goals_access,
                "samples": tk.samples_access,
            }
    return None

def update_token_last_used_date(db: Session, token: str) -> bool:
    tk = db.query(db_models.Auth).filter_by(token_value=token).first()
    if tk:
        tk.last_time_used = dt.now()
        db.commit()
        return True
    return False

def remove_user(db: Session, existing_user: db_models.User):
    user = db.merge(existing_user)
    print(db, existing_user)
    all_goals = db.query(db_models.Goal).filter_by(user_id=user.id).all()
    all_goals = [resources.Goal(
        id=g.id,
        title=g.title,
        average_target=g.average_target,
        end_datetime=g.end_datetime,
        start_datetime=g.start_datetime,
        stats_target=None,
        trend_target=resources.TrendState.from_integer(g.trend_target),
        status=resources.GoalStatus.from_integer(g.status)
    ) for g in all_goals]
    for g in all_goals:
        db.delete(g)
    print(db, existing_user)
    db.delete(user)
    print(db, existing_user)
    
    db.commit()
    return resources.AllUserInformation(
        account=resources.User(
            user_id=user.id,
            firstname=user.firstname,
            lastname=user.lastname,
            username=user.firstname+"_"+user.lastname
        ),
        goals=all_goals
    )

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
        title=title,
        status=status,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        average_target=average_target,
        trend_target=trend_target,
        minimum=minimum,
        maximum=maximum,
        stat_range=stat_range,
        mean=mean,
        variance=variance,
        std_dev=std_dev,
        overall_samples_size=overall_samples_size,
        first_quart=first_quart,
        second_quart=second_quart,
        third_quart=third_quart,
        median=median
    )
    db.add(g)
    db.commit()
    return g

def remove_goal(db: Session, goal_id: int) -> resources.Goal | None:
    existing_goal = db.query(db_models.Goal).filter_by(id=goal_id).first()
    if not existing_goal:
        return None
    db.delete(existing_goal)
    db.commit()
    g = resources.Goal(
        id=existing_goal.id,
        title=existing_goal.title,
        average_target=existing_goal.average_target,
        end_datetime=existing_goal.end_datetime,
        start_datetime=existing_goal.start_datetime,
        stats_target=None,
        trend_target=resources.TrendState.from_integer(existing_goal.trend_target),
        status=resources.GoalStatus.from_integer(existing_goal.status)
    )
    return g

def remove_all_goals(db: Session, user: db_models.User) -> list[resources.Goal]:
    all_goals = db.query(db_models.Goal).filter_by(user_id=user.id).all()
    for g in all_goals:
        db.delete(g)
    db.commit()
    return [resources.Goal(
        id=g.id,
        title=g.title,
        average_target=g.average_target,
        end_datetime=g.end_datetime,
        start_datetime=g.start_datetime,
        stats_target=None,
        trend_target=resources.TrendState.from_integer(g.trend_target),
        status=resources.GoalStatus.from_integer(g.status)
    ) for g in all_goals]


def update_goal_attribute(db: Session, goal_id: int, updatedKey: resources.UpdatedKey, new_value: resources.GoalAttr) ->resources.Goal | None:
    existing_goal = db.query(db_models.Goal).filter_by(id=goal_id).first()
    if not existing_goal:
        return None
    if updatedKey.name == 'title':
        existing_goal.title = new_value.value
    elif updatedKey.name == 'status':
        existing_goal.status = new_value.value
    elif updatedKey.name == 'start_datetime':
        existing_goal.start_datetime = new_value.value
    elif updatedKey.name == 'end_datetime':
        existing_goal.end_datetime = new_value.value
    db.commit()
    g = resources.Goal(
        id=existing_goal.id,
        title=existing_goal.title,
        average_target=existing_goal.average_target,
        end_datetime=existing_goal.end_datetime,
        start_datetime=existing_goal.start_datetime,
        stats_target=None,
        trend_target=resources.TrendState.from_integer(existing_goal.trend_target) if existing_goal.average_target else None,
        status=resources.GoalStatus.from_integer(existing_goal.status) if existing_goal.status else None
    )
    return g