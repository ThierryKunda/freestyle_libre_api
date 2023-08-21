import os
from typing import Literal

FRONT_END_APP_URI = os.getenv('FRONT_END_APP_URI', "sqlite:///./db.sqlite")
ENVIRONNEMENT: Literal['DEV', 'PROD'] = os.getenv('FLAPI_ENV', 'DEV')