import hashlib
from typing import Literal
from datetime import datetime as dt, time, timedelta as tdelta
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import desc

import models.database as db_models
import models.resources as resources

from statistics import mean
import pandas as pd

def encode_secret(secret: str) -> str:
    return hashlib.sha256(bytes(secret, encoding='utf-8')).hexdigest()

def get_user(db: Session, username: str, password: str):
    pw = encode_secret(password)
    try:
        firstname, lastname = username.split("_")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username should include \"_\" character between the firstname and the lastname."
        )
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
        user_profile_access: bool, samples_access: bool, goals_access: bool, stats_access: bool,
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
        creation_date=dt.now(),
        expiration_date=dt.now() + tdelta(days=days_from_unit(int(expiration_value), expiration_unit)),
        last_time_used=dt.now(),
        user_profile_access=user_profile_access,
        samples_access = samples_access,
        goals_access = goals_access,
        stats_access = stats_access,
    )
    db.add(tk)
    db.commit()
    return {
        "id": tk.id,
        "value": tk.token_value,
        "expiration_date": tk.expiration_date
    }

def get_user_from_token(db: Session, token: str) -> db_models.User | None:
    # Checks if token already exists
    tk = db.query(db_models.Auth).filter_by(token_value=token).first()
    if tk:
        # Do nothing if tokens is expired
        if tk.expiration_date < dt.now():
            return None
        return db.query(db_models.User).filter_by(id=tk.user_id).first()
    else:
        return None

def get_user_data(username: str):
    return pd.read_csv(f"./users_data/{username}.csv", sep=',', header=1, parse_dates=[2], date_format="%d-%m-%Y %H:%M")

def get_user_devices(user: db_models.User) -> list[str]:
    if user:
        user_data = get_user_data(user.firstname + "_" + user.lastname)
        return list(set(user_data["Appareil"]))
    return None

def get_user_tokens(db: Session, user_id: str):
    user_tokens = db.query(db_models.Auth).filter_by(user_id=user_id).all()
    return [
        resources.TokenDisplay(
            app_name=tk.app_name,
            token_value=tk.token_value,
            creation_date=tk.creation_date.strftime("%d/%m/%y-%H:%M"),
            expiration_date=tk.expiration_date.strftime("%d/%m/%y-%H:%M"),
            profile_right=tk.user_profile_access,
            samples_right=tk.samples_access,
            goals_right=tk.goals_access,
            stats_right=tk.stats_access,
        )
        for tk in user_tokens
    ]

def get_token_rights(db: Session, token: str) -> dict[str, bool] | None:
    # Checks if token exists
    tk = db.query(db_models.Auth).filter_by(token_value=token).first()
    if tk:
        if tk.expiration_date >= dt.now():
            return {
                "profile": tk.user_profile_access,
                "goals": tk.goals_access,
                "samples": tk.samples_access,
                "stats": tk.stats_access
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
    db.delete(user)
    
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

def request_new_password(db: Session, email_or_username: str):
    try:
        firstname, lastname = email_or_username.split("_")
    except ValueError:
        firstname, lastname = "", ""
    user = db.query(db_models.User).filter((db_models.User.email == email_or_username) \
                                           | ((db_models.User.firstname == firstname) & (db_models.User.lastname == lastname))).first()
    if not user:
        return resources.PasswordResponse(is_success=False, description="User not found 🕵️ : check your typed the email/usnername you used for registration.")
    new_pw_req = db_models.NewPasswordReq(user_id=user.id, change_req_id=encode_secret(email_or_username+str(user.id)+str(dt.now())), expiration_date=dt.now()+tdelta(days=2))
    db.add(new_pw_req)
    db.commit()
    return resources.PasswordResponse(is_success=True, description="Check your email inbox to define a new one. 😁")

def get_password_request(db: Session, change_req_id: str):
    req = db.query(db_models.NewPasswordReq).filter_by(change_req_id=change_req_id).first()
    if req:
        return req
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Password request does not exist for the id provided : {change_req_id}."
        )

def change_user_password(db: Session, change_req_id: str, new_password: str):
    new_pw_req = db.query(db_models.NewPasswordReq).filter_by(change_req_id=change_req_id).first()
    if not new_pw_req:
        return resources.PasswordResponse(is_success=False, description="Invalid new password request. 🤔")
    if new_pw_req.expiration_date < dt.now():
        return resources.PasswordResponse(is_success=False, description="Expired new password request. 🕰️")
    if new_pw_req.change_applied:
        return resources.PasswordResponse(is_success=False, description="New password request already used...🤷 Submit another one.")
    user = new_pw_req.user
    user.password = encode_secret(new_password)
    new_pw_req.change_applied = True
    db.commit()
    return resources.PasswordResponse(is_success=True, description="Password successfully changed/set. 😁")

def datetime_included_in_hour_interval(d: dt, t: time, e: int):
    ref_date = dt(year=d.year, month=d.month, day=d.day, hour=t.hour, minute=t.minute)
    return (d - tdelta(minutes=e)) <= ref_date <= (d + tdelta(minutes=e))

def average_from_samples(samples: list[resources.BloodGlucoseSample]):
    return mean([s.value for s in samples])

def get_user_average_day_user_samples(user: db_models.User, all_samples: dict[str, list[resources.BloodGlucoseSample]], hours: list[time], error: int):
    user_samples = all_samples[user.firstname+'_'+user.lastname]
    # Aggregate samples included in specific time interval
    samples_grouped_by_time_interval = {
        h: [s for s in user_samples if datetime_included_in_hour_interval(s.sampling_date, h, error)]
        for h in hours
    }
    # Compute the average for each interval
    samples_average_by_time_interval = {
        s: average_from_samples(samples_grouped_by_time_interval[s])
        for s in samples_grouped_by_time_interval
    }
    return [
        resources.AverageDaySample(hour=s, average_value=samples_average_by_time_interval[s])
        for s in samples_average_by_time_interval
    ]

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

def get_user_features_from_resource_name(resource_name: str, db: Session):
    resource = db.query(db_models.DocResource).filter_by(resource_name=resource_name, admin_privilege=False).first()
    if resource:
        features = db.query(db_models.DocFeature).filter_by(resource_id=resource.id, admin_privilege=False).all()
        return [resources.Feature(
            title=f.title,
            available=f.available,
            description=f.description,
            http_verb=f.http_verb.value,
            uri=f.uri
        )
        for f in features]
    return None

def get_all_resources(db: Session):
    return [resources.Resource(
        resource_name=r.resource_name,
        description=r.description
    )
        for r in db.query(db_models.DocResource).all()]

def get_admin_features_from_resource_name(resource_name: str, db: Session, user: db_models.User):
    # Checks if user is an administrator with doc management role
    admin_record = db.query(db_models.AdminManagement).filter_by(
        user_id=user.id
    ).order_by(
        db_models.AdminManagement.edit_date.desc()
    ).first()
    if admin_record and admin_record.manage_doc:
        resource = db.query(db_models.DocResource).filter_by(resource_name=resource_name).first()
        if resource:
            features = db.query(db_models.DocFeature).filter_by(resource_id=resource.id, admin_privilege=True).all()
            return [resources.Feature(
                title=f.title,
                available=f.available,
                description=f.description,
                http_verb=f.http_verb.value,
                uri=f.uri
            )
            for f in features]
        return None
    else:
        return False
    
def get_doc_info(db: Session):
    desc = db.query(db_models.DocSection).filter_by(title="description").first()
    auth = db.query(db_models.DocSection).filter_by(title="authentification").first()
    rights = db.query(db_models.DocSection).filter_by(title="rights").first()

    if desc and auth and rights:
        desc_content = [resources.BlockOfContent(title=b.title, content=b.content) for b in db.query(db_models.DocContentBlock).filter_by(doc_section_id=desc.id).all()]
        auth_content = [resources.BlockOfContent(title=b.title, content=b.content) for b in db.query(db_models.DocContentBlock).filter_by(doc_section_id=auth.id).all()]
        rights_content = [resources.BlockOfContent(title=b.title, content=b.content) for b in db.query(db_models.DocContentBlock).filter_by(doc_section_id=rights.id).all()]
        return resources.APIDocInfo(description=desc_content, authentification=auth_content, rights=rights_content)
    return None

def check_admin_is_allowed(db: Session, user_id: int, role_required: resources.AdminRole):
    is_admin = db.query(db_models.AdminManagement).filter_by(user_id=user_id).order_by(desc(db_models.AdminManagement.edit_date)).first()
    unauth = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You are not an admin or you do not have the right to perform this action."
        )
    if is_admin is None:
        raise unauth
    if role_required == resources.AdminRole.doc:
        if not is_admin.manage_doc:
            raise unauth
    elif role_required == resources.AdminRole.user:
        if not is_admin.manage_user:
            raise unauth
    elif role_required == resources.AdminRole.backup:
        if not is_admin.manage_backup:
            raise unauth
    else:
        raise unauth

def get_resources_info(db: Session, user_id: int):
    rs = db.query(db_models.DocResource).all()
    is_admin = db.query(db_models.AdminManagement).filter_by(user_id=user_id).order_by(desc(db_models.AdminManagement.edit_date)).first()
    unauth = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You are not an admin, you do not have the right to perform this action."
        )
    check_admin_is_allowed(db, user_id, resources.AdminRole.doc)
    return [
        resources.Resources(
            id=r.id,
            resource_name=r.resource_name,
            description=r.description,
        )
        for r in rs
    ]

def get_signatures(db: Session, user_id: int):
    check_admin_is_allowed(db, user_id, resources.AdminRole.doc)
    signatures = db.query(db_models.SecretSignature).all()
    return [
        resources.SecretSignature(
            id=s.id,
            secret_value=s.secret_value,
            generation_date=s.generation_date.strftime('%d/%m/%Y-%H:%M')
        )
        for s in signatures 
    ]