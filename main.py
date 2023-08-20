from routers.router_imports import *
import env

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[env.FRONT_END_APP_URI],
    allow_origin_regex=r'https?://(localhost|127\.0\.0\.1).*',
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

samples: dict[str, list[resources.BloodGlucoseSample]] = {}
stats = {key: resources.Stats.from_sample_collection(samples[key]) for key in samples}
# Default prefixes : profile samples goals stats
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={
    "profile": "Read information about user profile",
    "samples": "Read samples related to a user",
    "goals": "Read user goals",
    "stats": "Read user statistics"
})

def lazy_load_user_data(username: str):
    if username not in samples:
        user_data = api.samples_from_csv(filepath=os.path.join("users_data", f"{username}.csv"))
        if user_data:
            samples[username] = user_data
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User data not found, based on username"
            )
def lazy_load_user_stats(username):
    if username not in stats:
        if username in samples:
            stats[username] = resources.Stats.from_sample_collection(samples[username])
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User data not found, based on username"
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

def map_access_form_inputs(
        inputs: list[str] = ["not_allowed", "not_allowed", "not_allowed"],
        mappings: dict[str, bool] = {"allowed": True, "not_allowed": False},
        in_place: bool = False,
        input_prefixed: bool = False,
    ) -> list[bool]:
    # Default prefixes : profile samples goals stats
    if input_prefixed:
        res = [False, False, False, False]
        for s in inputs:
            if s.startswith("profile"):
                allowing = s.split(":")[1]
                res[0] = mappings[allowing]
            elif s.startswith("samples"):
                allowing = s.split(":")[1]
                res[1] = mappings[allowing]
            elif s.startswith("goals"):
                allowing = s.split(":")[1]
                res[2] = mappings[allowing]
            elif s.startswith("stats"):
                allowing = s.split(":")[1]
                res[3] = mappings[allowing]

        return res
    elif in_place:
        rights = ["profile", "samples", "goals", "stats"]
        res = [True if s in inputs else False for s in rights]
        return res
        # return res
    return [mappings[inputs[i]] for i in range(len(inputs))]

async def get_authorized_user(security_scopes: SecurityScopes, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    utils.update_token_last_used_date(db, token)
    if security_scopes.scopes:
        authentificate_value = f'Bearer scope="{security_scopes.scope_str}"'
        rights = utils.get_token_rights(db, token)
        unauth_expection = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission to perform any action on specified resource(s)",
            headers={"WWW-Authenticate": authentificate_value}
        )
        if rights:
            for r in security_scopes.scopes:
                if not rights[r]:
                    raise unauth_expection
                    # if not r in security_scopes.scopes:
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token does not exist or is already expired",
                headers={"WWW-Authentificate": authentificate_value}
            )
    else:
        authentificate_value = 'Bearer'
    user = utils.get_user_from_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authentificate_value}
        )
    return user

def check_username(username: str, user: User) -> None:
    if username != user.firstname + '_' + user.lastname:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token with username")

@app.get("/")
async def read_root():
    f = open("pages/index.html", "r")
    content = f.read()
    f.close()
    return HTMLResponse(content=content)


@app.post("/user")
async def new_user(user: resources.CreateUser, db: Session = Depends(get_db)):
    new_user = utils.add_new_user(db, user.firstname, user.lastname, user.password)
    if new_user:
        tk = utils.add_new_token(db, user.firstname, user.lastname, user.password, True, True, True, 1, "days")
        return tk
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

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
        samples[f'{firstname}_{lastname}'] = api.samples_from_csv(filepath=os.path.join("users_data", p))
        stats[f'{firstname}_{lastname}'] = resources.Stats.from_sample_collection(samples[f"{firstname}_{lastname}"])
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
    print(access_rights)
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

@app.get("/user")
async def get_user_infos(user: User = Security(get_authorized_user, scopes=['profile'])):
    return resources.User(
        user_id=user.id,
        firstname=user.firstname,
        lastname=user.lastname,
        username=user.firstname+"_"+user.lastname,
        email=user.email,
        devices_list=utils.get_user_devices(user)
    )

@app.delete("/user")
async def remove_user_account(db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['profile', 'samples', 'goals'])):
    all_info = utils.remove_user(db, user)
    print("User deleted")
    return all_info

@app.get("/user/{username}/raw_data")
async def get_user_data_file(username: str, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    return FileResponse(os.path.join("users_data", f"{username}.csv"))

@app.post("/user/{username}/raw_data")
async def add_or_update_user_data_file(username: str, file: UploadFile, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    content_bytes = await validate_data_from_upload(file)
    f = open(os.path.join("users_data", f"{username}.csv"), "wb")
    f.write(content_bytes)
    return resources.UserDataFileUpdateResponse(message="User data file was successfully updated.")


@app.post("/submit_password_change")
async def req_new_password(req_params: resources.ReqNewPasswordParameters, db: Session = Depends(get_db)):
    return utils.request_new_password(db, req_params.email)

@app.put("/user/{username}/set_new_password")
async def change_password(username: str, change_req_id: str, req_params: resources.ChangePasswordParameters, db: Session = Depends(get_db)):
    return utils.change_user_password(db, change_req_id, username, req_params.new_password)

@app.get("/user/{username}/samples")
async def read_samples(username: str, day: Optional[str] = None, user: User = Security(get_authorized_user, scopes=['samples'])) -> list[resources.BloodGlucoseSample]:
    check_username(username, user)
    lazy_load_user_data(username)
    if day is None:
        res = list(filter(lambda d: d.sampling_date.date() == datetime.today().date(), samples[username]))
        if len(res) == 0:
            raise HTTPException(status_code=404)
        return res
    try:
        return list(filter(lambda d: datetime.strptime(day, "%d/%m/%Y").date() == d.sampling_date.date(), samples[username]))
    except ValueError:
        error_message = {
            "resource_type": "sample",
            "username": username,
            "error_description": "The date input is invalid" 
        }
        raise HTTPException(status_code=400, detail=error_message)

@app.get("/user/{username}/samples/latest")
async def read_latest_samples(username: str, n_latest: Optional[int] = None, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    n = len(samples[username])
    if n_latest:
        return samples[username][n-(n_latest-1):n]
    return samples[username][n-5:n]

@app.post("/user/{username}/samples/average_day")
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
    return utils.get_user_average_day_user_samples(user, samples, hours, req_params.error)

@app.get("/user/{username}/stats")
def read_user_stats(username: str, user: User = Security(get_authorized_user, scopes=['profile'])):
    check_username(username, user)
    lazy_load_user_data(username)
    lazy_load_user_stats(username)
    return stats[username]

@app.get("/users/stats")
def read_stats(_: User = Security(get_authorized_user, scopes=['profile'])):
    # Load data from all users
    samples = {data.split('_')[0]+"_"+data.split('_')[1]: api.samples_from_csv(filepath=os.path.join("users_data", f"{data}")) for data in os.listdir("users_data")}
    return resources.Stats.from_all_users_samples(samples)

@app.get("/user/{username}/trend/hours_interval")
def read_trend_hours(username: str, h1_string: str, h2_string: str, error: int, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    h1 = datetime.strptime(h1_string, "%d/%m/%Y-%H:%M")
    h2 = datetime.strptime(h2_string, "%d/%m/%Y-%H:%M")
    return resources.HourTrend.from_hours(h1,h2,samples[username], error)

@app.get("/user/{username}/trend/days_interval")
def read_trend_days(username: str, day1_string: str, day2_string: str, error: int, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username)
    lazy_load_user_data(username)
    username = user.firstname + '_' + user.lastname
    day1 = datetime.strptime(day1_string, "%d/%m/%Y")
    day2 = datetime.strptime(day2_string, "%d/%m/%Y")
    return resources.HourTrend.from_hours(day1,day2,samples[username], error)

@app.get("/user/{username}/trend/months_interval")
def read_trend_months(username: str, month1: int, year1: int, month2: int, year2: int, error: int, user: User = Security(get_authorized_user, scopes=['samples'])):
    check_username(username, user)
    lazy_load_user_data(username)
    return resources.MonthTrend.from_months(month1, year1, month2, year2, samples[username], error)

@app.get("/user/{username}/goals")
def get_all_goals(username: str, db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['goals'])) -> list[resources.Goal]:
    check_username(username, user)
    return utils.get_user_goals(db, user)

@app.post("/user/{username}/goal/")
def add_new_goal(username: str, goal: resources.Goal, user: User = Security(get_authorized_user, scopes=['goals']), db: Session = Depends(get_db)) -> resources.Goal:
    check_username(username, user)
    g = utils.add_new_goal(
        db,
        user,
        goal.title,
        goal.status.to_integer(),
        start_datetime=goal.start_datetime,
        end_datetime=goal.end_datetime,
        average_target=goal.average_target,
        trend_target=goal.trend_target.to_integer(),
        stat_range=goal.stats_target.stat_range,
        minimum=goal.stats_target.minimum,
        maximum=goal.stats_target.maximum,
        mean=goal.stats_target.mean,
        median=goal.stats_target.median,
        first_quart=goal.stats_target.first_quartile,
        second_quart=goal.stats_target.second_quartile,
        third_quart=goal.stats_target.third_quartile,
        overall_samples_size=goal.stats_target.overall_samples_size,
        variance=goal.stats_target.variance,
        std_dev=goal.stats_target.standard_deviation
    )
    if not g:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Based on the title, goal already exists"
        )
    goal.id = g.id
    return goal

@app.delete("/user/{username}/goal/{id}")
def remove_goal(username: str, id: int, user: User = Security(get_authorized_user, scopes=['goals']), db: Session = Depends(get_db)) -> resources.Goal:
    check_username(username, user)
    g = utils.remove_goal(db, id)
    if not g:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="There is no goal with this identifier"
        )
    return g

@app.patch("/user/{username}/goal/{id}")
def update_goal_element(username: str, id: int, updatedKey: resources.UpdatedKey, new_value: resources.GoalAttr, user: User = Security(get_authorized_user, scopes=['goals']), db: Session = Depends(get_db)) -> resources.Goal:
    check_username(username, user)
    g = utils.update_goal_attribute(db, id, updatedKey, new_value)
    if not g:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="There is no goal with this identifier"
        )
    return g

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