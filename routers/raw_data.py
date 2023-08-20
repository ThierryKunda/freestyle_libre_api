from fastapi import APIRouter

from router_dependencies import *

router = APIRouter(tags=["Raw data"])

@router.get("/user/{username}/raw_data")
async def get_user_data_file(username: str, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    return FileResponse(os.path.join("users_data", f"{username}.csv"))

@router.post("/user/{username}/raw_data")
async def add_or_update_user_data_file(username: str, file: UploadFile, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    content_bytes = await validate_data_from_upload(file)
    f = open(os.path.join("users_data", f"{username}.csv"), "wb")
    f.write(content_bytes)
    return resources.UserDataFileUpdateResponse(message="User data file was successfully updated.")