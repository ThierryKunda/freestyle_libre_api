import os
from typing import Literal

FRONT_END_APP_URI = os.environ['FRONT_END_APP_URI']
try:
    SQLALCHEMY_DATABASE_URL: Literal['DEV', 'PROD'] = os.environ['DB_URL']
except KeyError:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite"
ENVIRONNEMENT = os.environ['FLAPI_ENV']