import os

# Base, Development and Production classes.

class BaseConfig(object):
    SECRET_KEY = os.getenv("SECRET_KEY", "topsecret")
    #FLASK_APP = os.getenv("FLASK_APP", "geneplexus_app")
    MAX_NUM_GENES = 50
    # prefix for finding all backend data.   Must end with path separtor
    # currently POSIX only
    DATA_PATH = os.getenv('DATA_PATH','./app/data_backend') + "/" 
    JOB_PATH  = os.getenv('JOB_PATH', './app/jobs') + "/"
    LOG_FILE = os.getenv('LOG_FILE', 'geneplexus_app.log')
    
    # backend container information
    JOB_IMAGE_NAME = os.getenv('JOB_IMAGE_NAME','geneplexus-backend')
    JOB_IMAGE_TAG  = os.getenv('JOB_IMAGE_TAG', 'latest')
    # secrets needed for launching batch jobs on azure
    STORAGE_ACCOUNT_KEY = os.getenv('STORAGE_ACCOUNT_KEY', '')
    CONTAINER_REGISTRY_PW = os.getenv('CONTAINER_REGISTRY_PW', '')
    BASE_CONTAINER_PATH = os.getenv('BASE_CONTAINER_PATH', '')
    JOB_URL = os.getenv('JOB_URL', '')

class ProdConfig(BaseConfig):
    FLASK_ENV="production"
    FILE_LOC = "local"

class DevConfig(BaseConfig):
    FLASK_ENV="development"
    FLASK_DEBUG="1"
    FILE_LOC = "local"
