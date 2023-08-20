import os
from typing import Literal

FRONT_END_APP_URI = os.environ['FRONT_END_APP_URI']
try:
    SQLALCHEMY_DATABASE_URL = os.environ['DB_URL']
except KeyError:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite"
try:
    ENVIRONNEMENT: Literal['DEV', 'PROD'] = os.environ['FLAPI_ENV']
except KeyError:
    ENVIRONNEMENT = 'DEV'