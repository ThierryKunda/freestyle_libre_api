from typing import List

from router_dependencies import *

router = APIRouter(tags=["Samples"])

@router.get("/{username}/samples")
async def read_samples(username: str, day: Optional[str] = None, user: User = Security(get_authorized_user, scopes=['samples'])) -> List[resources.BloodGlucoseSample]:
    check_username(username, user)
    lazy_load_user_data(username)
    if day is None:
        res = list(filter(lambda d: d.sampling_date.date() == datetime.today().date(), samples_collection[username]))
        if len(res) == 0:
            raise HTTPException(status_code=404)
        return res
    try:
        return list(filter(lambda d: datetime.strptime(day, "%d/%m/%Y").date() == d.sampling_date.date(), samples_collection[username]))
    except ValueError:
        error_message = {
            "resource_type": "sample",
            "username": username,
            "error_description": "The date input is invalid" 
        }
        raise HTTPException(status_code=400, detail=error_message)

@router.get("/{username}/samples/latest")
async def read_latest_samples(username: str, n_latest: Optional[int] = None, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    n = len(samples_collection[username])
    if n_latest:
        return samples_collection[username][n-(n_latest-1):n]
    return samples_collection[username][n-5:n]

@router.post("/{username}/samples/average_day")
async def get_user_samples_as_average_day(username: str, req_params: resources.AverageDayParams, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    try:
        hours = [datetime.strptime(h, "%H:%M").time() for h in req_params.hours]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours format not respected : HH:MM"
        )
    return utils.get_user_average_day_user_samples(user, samples_collection, hours, req_params.error)