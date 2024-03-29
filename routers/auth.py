from fastapi import APIRouter

from router_dependencies import *

router = APIRouter(tags=["Auth"])

@router.get("/tokens")
async def get_tokens_list(db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['profile', 'samples', 'goals', 'stats'])):
    return utils.get_user_tokens(db, user.id)

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = utils.get_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    firstname, lastname = form_data.username.split("_")
    # Scopes format -> profile samples goals stats
    access_rights = map_access_form_inputs(inputs=form_data.scopes, in_place=True)
    tk = utils.add_new_token(db, firstname, lastname, form_data.password, access_rights[0], access_rights[1], access_rights[2], access_rights[3])
    if not tk:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="The token can not be generated for the time being.\nPlease be patient until the problem is resolved.",
            headers={
                "Retry-After": (60 * 60 * 24)
            }
        )
    return tk

@router.post("/submit_password_change")
async def req_new_password(req_params: resources.ReqNewPasswordParameters, db: Session = Depends(get_db)):
    return utils.request_new_password(db, req_params.email_or_username)

@router.get("/new_password_request")
async def get_password_request(change_req_id: str, db: Session = Depends(get_db)):
    return utils.get_password_request(db, change_req_id)


@router.post("/new_password/{change_req_id}")
async def change_password(change_req_id: str, req_params: resources.ChangePasswordParameters, db: Session = Depends(get_db)):
    return utils.change_user_password(db, change_req_id, req_params.new_password)
