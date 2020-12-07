import os

# Base, Development and Production classes.

class BaseConfig(object):
    SECRET_KEY = os.getenv("SECRET_KEY", "topsecret")
    #FLASK_APP = os.getenv("FLASK_APP", "geneplexus_app")
    MAX_NUM_GENES = 1000
    DATA_PATH = os.getenv('DATA_PATH', './app/data_backend/')

class ProdConfig(BaseConfig):
    FLASK_ENV="production"
    FILE_LOC = "cloud"


class DevConfig(BaseConfig):
    FLASK_ENV="development"
    FLASK_DEBUG="1"
    FILE_LOC = "local"