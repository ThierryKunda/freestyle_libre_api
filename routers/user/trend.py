from fastapi import APIRouter

from router_dependencies import *

router = APIRouter(tags=["Trends"])

@router.get("/user/{username}/trend/hours_interval")
def read_trend_hours(username: str, h1_string: str, h2_string: str, error: int, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    h1 = datetime.strptime(h1_string, "%d/%m/%Y-%H:%M")
    h2 = datetime.strptime(h2_string, "%d/%m/%Y-%H:%M")
    return resources.HourTrend.from_hours(h1,h2,samples_collection[username], error)

@router.get("/user/{username}/trend/days_interval")
def read_trend_days(username: str, day1_string: str, day2_string: str, error: int, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username)
    lazy_load_user_data(username)
    username = user.firstname + '_' + user.lastname
    day1 = datetime.strptime(day1_string, "%d/%m/%Y")
    day2 = datetime.strptime(day2_string, "%d/%m/%Y")
    return resources.HourTrend.from_hours(day1,day2,samples_collection[username], error)

@router.get("/user/{username}/trend/months_interval")
def read_trend_months(username: str, month1: int, year1: int, month2: int, year2: int, error: int, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    return resources.MonthTrend.from_months(month1, year1, month2, year2, samples_collection[username], error)
