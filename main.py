from router_dependencies import *
import env

from routers import user, stats

app = FastAPI()

app.include_router(user.router)
app.include_router(stats.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[env.FRONT_END_APP_URI],
    allow_origin_regex=r'https?://(localhost|127\.0\.0\.1).*',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

def render_html_error_message(message: str, status_code: int):
    f = open("pages/error.html", "r")
    content = f.read().replace("[[error_description]]", message)
    f.close()
    return HTMLResponse(content=content, status_code=status_code)

def render_html_page(title: str, body: str):
    return HTMLResponse("""<!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{}</title>
    </head>
    <body>
    {}
    </body>
    </html>""".format(title, body))


@app.get("/")
async def read_root():
    f = open("pages/index.html", "r")
    content = f.read()
    f.close()
    return HTMLResponse(content=content)



@app.get("/new_account")
async def create_new_account():
    return render_html_page("New account", """
        <h1>Create a new account</h1>
        <form action="/account_created" method="POST" enctype="multipart/form-data">
        <label for="firstname">First name : </label>
        <input type="text" name="firstname" id="firstname" required>
        <label for="lastname">Last name : </label>
        <input type="text" name="lastname" id="lastname" required>
        <label for="lastname">Password : </label>
        <input type="password" name="password" id="password" required>
        <input type="submit" value="Create new account">
        </form>
    """)

@app.post("/account_created")
async def account_created(
    db: Session = Depends(get_db), firstname: str = Form(),
    lastname: str = Form(), password: str = Form()
    ):
    user = utils.add_new_user(db, firstname=firstname, lastname=lastname, password=password)
    if user:
        return render_html_page("New account created", "<h1>New account created !</h1>")
    else:
        return render_html_error_message("user already exists", 403)

@app.get("/new_access_token")
async def new_access_token_form():
    return render_html_page("New access token", """
        <h1>Create a new access token</h1>
        <form action="/access_token_created" method="POST" enctype="multipart/form-data">
        <label for="firstname">First name : </label>
        <input type="text" name="firstname" id="firstname" required>
        <label for="lastname">Last name : </label>
        <input type="text" name="lastname" id="lastname" required>
        <label for="lastname">Password : </label>
        <input type="password" name="password" id="password" required>
        <label for="user-profile">User profile access</label>
        <select name="user-profile" id="user-profile" required>
            <option value="allowed">Allow</option>
            <option value="not_allowed">Do not allow</option>
        </select>
        <label for="samples">User profile access</label>
        <select name="samples" id="samples" required>
            <option value="allowed">Allow</option>
            <option value="not_allowed">Do not allow</option>
        </select>
        <label for="goals">User profile access</label>
        <select name="goals" id="goals" required>
            <option value="allowed">Allow</option>
            <option value="not_allowed">Do not allow</option>
        </select>
        <label for="duration-value">Token duration</label>
        <input type="number" min="0" name="duration-value" />
        <select name="duration-unit" id="duration-unit" required>
            <option value="days">day(s)</option>
            <option value="months">month(s)</option>
            <option value="years">year(s)</option>
        </select>
        <input type="submit" value="Create token">
        </form>
    """)

@app.post("/access_token_created")
async def create_new_access_token(
    db: Session = Depends(get_db), firstname: str = Form(), lastname: str = Form(),
    password: str = Form(), user_profile_access: str = Form(alias="user-profile"),
    samples_access: str = Form(alias="samples"), goals_access: str = Form(alias="goals"),
    duration_unit: str = Form(alias="duration-unit"), duration_value: str = Form(alias="duration-value")
    ):
    access_mapping = map_access_form_inputs([user_profile_access, samples_access, goals_access])
    tk = utils.add_new_token(
        db, firstname, lastname, password,
        user_profile_access=access_mapping[0],
        samples_access=access_mapping[1],
        goals_access=access_mapping[2],
        expiration_unit=duration_unit,
        expiration_value=duration_value
    )
    if not tk:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="The token cannot be generated for the time being.\nPlease be patient until the problem is resolved.",
            headers={
                "Retry-After": (60 * 60 * 24)
            }
        )
    return tk

@app.post("/file_uploaded")
async def upload_csv_data(
    personal_data: UploadFile, firstname: str = Form(), lastname: str = Form(),
    db: Session = Depends(get_db), token: str = Form(alias="access-token")
    ):
    # The right "user_profile" provided by the access token is checked  
    rights = utils.get_token_rights(db, token)
    if not rights["profile"]:
        return render_html_error_message("The access token does not provide the right to add or delete user's medical data", 403)
    try:
        if firstname == '' or lastname == '':
            return render_html_error_message("No firstname or lastname input", status.HTTP_404_NOT_FOUND)
        # today_str = datetime.today().strftime("%d-%m-%Y")
        # Creating the CSV file for data storing
        p = f"{firstname}_{lastname}.csv"
        f_data = open(os.path.join("users_data", p), "wb")
        file_content = await personal_data.read()
        f_data.write(file_content)
        f_data.close()
        samples_collection[f'{firstname}_{lastname}'] = api.samples_from_csv(filepath=os.path.join("users_data", p))
        stats_collection[f'{firstname}_{lastname}'] = resources.Stats.from_sample_collection(samples_collection[f"{firstname}_{lastname}"])
        # Web page
        f = open("pages/file_uploaded.html", "r")
        content = f.read().replace("[[content]]", personal_data.filename)
        f.close()
        return HTMLResponse(content=content, status_code=200)
    except IOError:
        # Displaying error page if file input handling failed
        return render_html_error_message("file handling failed", 500)
    except IndexError:
        return render_html_error_message("one or more rows does not have a good number of cells", 400)
    except ValueError:
        # Displaying error page if a row has an invalid value
        return render_html_error_message("one or more rows have an invalid value", 400)

@app.get("/tokens")
async def get_tokens_list(db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['profile', 'samples', 'goals', 'stats'])):
    return utils.get_user_tokens(db, user.id)

@app.post("/token")
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
    return resources.Token(access_token=tk["value"], token_type="bearer")

@app.post("/submit_password_change")
async def req_new_password(req_params: resources.ReqNewPasswordParameters, db: Session = Depends(get_db)):
    return utils.request_new_password(db, req_params.email)

@app.put("/user/{username}/set_new_password")
async def change_password(username: str, change_req_id: str, req_params: resources.ChangePasswordParameters, db: Session = Depends(get_db)):
    return utils.change_user_password(db, change_req_id, username, req_params.new_password)

@app.get("/doc/resources")
async def get_all_resources_info(db: Session = Depends(get_db)):
    return utils.get_all_resources(db)

@app.get("/doc/resource/{resource_name}/features")
async def get_resource_features(resource_name: str, db: Session = Depends(get_db)):
    res = utils.get_user_features_from_resource_name(resource_name, db)
    if res:
        return res
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The resource \"{resource_name}\" does not exist"
        )
    
@app.get("/doc/admin/resources/{resource_name}/features")
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
    
@app.get("/doc/general_information")
async def get_doc_information(db: Session = Depends(get_db)):
    res = utils.get_doc_info(db)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missing documentation."
        )
    return res

@app.get("/doc/resources_data")
async def get_resources_data(db: Session = Depends(get_db), user: User = Security(get_authorized_user)):
    return utils.get_resources_info(db, user.id)

@app.get("/doc/signatures")
async def get_secret_signatures(db: Session = Depends(get_db), user: User = Security(get_authorized_user)):
    return utils.get_signatures(db, user.id)

# @app.get("/doc/db_metadata")
# async def get_db_versioning(db: Session = Depends(get_db), user: User = Security(get_authorized_user)):
#     pass