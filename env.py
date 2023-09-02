import os
from typing import Literal

PORT = os.getenv('PORT', "8000")
SQLALCHEMY_DATABASE_URL = os.getenv('DB_URL', "sqlite:///./db.sqlite")
FRONT_END_APP_URI = os.getenv('FRONT_END_APP_URI', "http://localhost:3000")
ENVIRONNEMENT: Literal['DEV', 'PROD'] = os.getenv('FLAPI_ENV', 'DEV')