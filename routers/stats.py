from fastapi import APIRouter

from router_dependencies import *

router = APIRouter(tags=["Stats"])

@router.get("/user/{username}/stats")
def read_user_stats(username: str, user: User = Security(get_authorized_user, scopes=['profile'])):
    check_username(username, user)
    lazy_load_user_data(username)
    lazy_load_user_stats(username)
    return stats_collection[username]

@router.get("/users/stats")
def read_stats(_: User = Security(get_authorized_user, scopes=['profile'])):
    # Load data from all users
    samples = {data.split('_')[0]+"_"+data.split('_')[1]: csv_data.samples_from_csv(filepath=os.path.join("users_data", f"{data}")) for data in os.listdir("users_data")}
    return resources.Stats.from_all_users_samples(samples)