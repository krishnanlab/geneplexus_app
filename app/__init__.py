from flask import Flask
from config import ProdConfig, DevConfig
from dotenv import load_dotenv
import logging
from pathlib import Path
from app.notifier import Notifier
from app.jobs import job_status_codes

# note : if using 'flask run' from command line this is unecessary as flask autoamtiaclly read .flaskenv
load_dotenv('.flaskenv')
# load instance specific config
load_dotenv('.env')  

app = Flask(__name__)
app.config['SECRET_KEY'] = 'something-no-one-would-guess'

if app.env == 'production':
    app.config.from_object(ProdConfig)
elif app.env == 'development':
    app.config.from_object(DevConfig)

logfile=app.config.get('LOG_FILE')

if not Path(logfile).exists():
    Path(logfile).touch()

logging.basicConfig(filename=app.config.get('LOG_FILE'),level=logging.INFO)
# TODO actually create a logger
# logger = logging.getLogger('app')

# job_folder configuration
job_folder = Path(app.config.get('JOB_PATH'))
if not job_folder.exists():
    job_folder.mkdir()

app.notifier = Notifier(app.config, job_status_codes, template_folder = 'templates')

#TODO do we need this here?
from app import views, models
