from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from router_dependencies import *

router = APIRouter(include_in_schema=False)

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


@router.get("/")
async def read_root():
    f = open("pages/index.html", "r")
    content = f.read()
    f.close()
    return HTMLResponse(content=content)

@router.get("/new_account")
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

@router.post("/account_created")
async def account_created(
    db: Session = Depends(get_db), firstname: str = Form(),
    lastname: str = Form(), password: str = Form()
    ):
    user = utils.add_new_user(db, firstname=firstname, lastname=lastname, password=password)
    if user:
        return render_html_page("New account created", "<h1>New account created !</h1>")
    else:
        return render_html_error_message("user already exists", 403)

@router.get("/new_access_token")
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

@router.post("/access_token_created")
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

@router.post("/file_uploaded")
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
        # Creating the CSV file for data storing
        p = f"{firstname}_{lastname}.csv"
        f_data = open(os.path.join("users_data", p), "wb")
        file_content = await validate_data_from_upload(personal_data)
        f_data.write(file_content)
        f_data.close()
        samples_collection[f'{firstname}_{lastname}'] = csv_data.samples_from_csv(filepath=os.path.join("users_data", p))
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