from flask import Flask, session
from config import ProdConfig, DevConfig
from dotenv import load_dotenv
from datetime import timedelta
from flask_session import Session

import logging
from pathlib import Path
from mljob.notifier import Notifier

# note : if using 'flask run' from command line this is unecessary as flask autoamtiaclly read .flaskenv
load_dotenv('.flaskenv')
# load instance specific config
load_dotenv('.env')  

app = Flask(__name__)
app.config['SECRET_KEY'] = 'something-no-one-would-guess'
SESSION_TYPE = 'filesystem'

if app.env == 'production':
    app.config.from_object(ProdConfig)
elif app.env == 'development':
    app.config.from_object(DevConfig)

logfile=app.config.get('LOG_FILE')
logging.basicConfig(filename=app.config.get('LOG_FILE'),level=logging.INFO)

app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=48)
app.config['SESSION_FILE_THRESHOLD'] = 500  


if not Path(logfile).exists():
    Path(logfile).touch()


# job_folder configuration
job_folder = Path(app.config.get('JOB_PATH'))
if not job_folder.exists():
    job_folder.mkdir()

app.notifier = Notifier(app.config, template_folder = 'templates')

from mljob import geneplexus
geneplexus.set_config(app.config)

from app import views

session = Session(app)
