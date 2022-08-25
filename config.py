import os

# Base, Development and Production classes.

class BaseConfig(object):
    BASE_URL = os.getenv('BASE_URL', '')
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
    STORAGE_ACCOUNT_NAME=os.getenv('STORAGE_ACCOUNT_NAME', '')
    STORAGE_SHARE_NAME=os.getenv('STORAGE_SHARE_NAME','')
    STORAGE_ACCOUNT_KEY = os.getenv('STORAGE_ACCOUNT_KEY', '')

    CONTAINER_REGISTRY_URL= os.getenv('CONTAINER_REGISTRY_URL','')
    CONTAINER_REGISTRY_USER = os.getenv('CONTAINER_REGISTRY_USER','')
    CONTAINER_REGISTRY_PW = os.getenv('CONTAINER_REGISTRY_PW', '')

    # used in the JSON sent to the trigger, that are sent to container launcher
    JOB_CONTAINER_FILE_MOUNT = os.getenv('JOB_CONTAINER_FILE_MOUNT', '' )
    
    JOB_URL = os.getenv('JOB_URL', '')  # the URL for the logic app trigger

    # email config
    SENDGRID_API_KEY= os.getenv('SENDGRID_API_KEY', '')
    NOTIFIER_EMAIL_ADDRESS = os.getenv('NOTIFIER_EMAIL_ADDRESS' )
    # this is the dev address used for testing job notification
    # TODO remove this from base config, but leave it here until email notification is implemented
    TEST_EMAIL_RECIPIENT = os.getenv('TEST_EMAIL_RECIPIENT')

    MAX_PREFIX_LENGTH = 32
    QUEUE_URL = os.getenv('QUEUE_URL', "")


    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GITHUB_ID = os.getenv('GITHUB_ID', '')
    GITHUB_SECRET = os.getenv('GITHUB_SECRET', '')

class ProdConfig(BaseConfig):
    FLASK_ENV="production"
    FILE_LOC = "local"

class DevConfig(BaseConfig):
    FLASK_ENV="development"
    FLASK_DEBUG="1"
    FILE_LOC = "local"
    # this is the dev address used for testing job notification
    TEST_EMAIL_RECIPIENT = os.getenv('TEST_EMAIL_RECIPIENT')
    # set this to force the jobs to run on the same machine
    RUN_LOCAL = (os.getenv('RUN_LOCAL', 'False').lower() == 'true')
    DEBUG = (os.getenv('DEBUG', 'False').lower() == 'true')
