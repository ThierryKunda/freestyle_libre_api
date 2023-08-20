from fastapi import APIRouter

from router_dependencies import *

router = APIRouter(tags=["Documentation"])

@router.get("/doc/resources")
async def get_all_resources_info(db: Session = Depends(get_db)):
    return utils.get_all_resources(db)

@router.get("/doc/resource/{resource_name}/features")
async def get_resource_features(resource_name: str, db: Session = Depends(get_db)):
    res = utils.get_user_features_from_resource_name(resource_name, db)
    if res:
        return res
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The resource \"{resource_name}\" does not exist"
        )
    
@router.get("/doc/admin/resources/{resource_name}/features")
async def get_admin_resource_features(resource_name: str, user: User = Security(get_authorized_user), db: Session = Depends(get_db)):
    res = utils.get_admin_features_from_resource_name(resource_name, db, user)
    if res:
        return res
    elif res is False:
        pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You do not have the right to perform this action."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The resource '{resource_name}' does not exist."
        )


@router.get("/doc/general_information")
async def get_doc_information(db: Session = Depends(get_db)):
    res = utils.get_doc_info(db)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missing documentation."
        )
    return res

@router.get("/doc/resources_data")
async def get_resources_data(db: Session = Depends(get_db), user: User = Security(get_authorized_user)):
    return utils.get_resources_info(db, user.id)

@router.get("/doc/signatures")
async def get_secret_signatures(db: Session = Depends(get_db), user: User = Security(get_authorized_user)):
    return utils.get_signatures(db, user.id)

# @app.get("/doc/db_metadata")
# async def get_db_versioning(db: Session = Depends(get_db), user: User = Security(get_authorized_user)):
#     pass