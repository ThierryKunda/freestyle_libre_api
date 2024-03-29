from router_dependencies import *
from routers.user import samples, trend, goal, raw_data

router = APIRouter(prefix='/user', tags=["User"])
router.include_router(samples.router)
router.include_router(trend.router)
router.include_router(goal.router)
router.include_router(raw_data.router)

@router.get("")
async def get_user_infos(user: User = Security(get_authorized_user, scopes=['profile'])):
    return resources.User(
        user_id=user.id,
        firstname=user.firstname,
        lastname=user.lastname,
        username=user.firstname+"_"+user.lastname,
        email=user.email,
        devices_list=utils.get_user_devices(user)
    )

@router.post("")
async def new_user(user: resources.CreateUser, db: Session = Depends(get_db)):
    new_user = utils.add_new_user(db, user.firstname, user.lastname, user.email, user.password)
    if new_user:
        tk = utils.add_new_token(db, user.firstname, user.lastname, user.password, True, True, True, True)
        return tk
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
@router.delete("")
async def remove_user_account(db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['profile', 'samples', 'goals'])):
    all_info = utils.remove_user(db, user)
    return all_info

@router.get("/role")
async def get_user_role(db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['profile', 'samples', 'goals', 'stats'])):
    return utils.get_user_role(db, user)