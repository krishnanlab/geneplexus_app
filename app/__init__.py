from urllib.error import URLError
from urllib.parse import urlparse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask.cli import with_appcontext
from flask_login import LoginManager, current_user
import click
from config import ProdConfig, DevConfig
from dotenv import load_dotenv
import logging
from pathlib import Path
from os import path

# system is based on file storage, but allows for writing a blob storage
from mljob.results_storage import ResultsFileStore as ResultsStore
from mljob.job_manager import JobManager, LocalLauncher, UrlLauncher
from mljob.notifier import Notifier

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

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)

from app.oauth.github import github_blueprint
app.register_blueprint(github_blueprint)
if not Path(logfile).exists():
    Path(logfile).touch()

logging.basicConfig(filename=app.config.get('LOG_FILE'),level=logging.INFO)
# TODO maybe name the logger
logger = logging.getLogger('app')

 
# job_folder configuration
# job_folder = Path(app.config.get('JOB_PATH'))
# if not job_folder.exists():
#     job_folder.mkdir()


# object to read/write all job-related info and results
results_store = ResultsStore(app.config.get('JOB_PATH'), create_if_missing=True)

# object to kick off jobs
if app.config.get('RUN_LOCAL'):
    
    launcher = LocalLauncher(app.config['DATA_PATH'], 
                    results_store = results_store, 
                    callback_url = path.join(app.config['BASE_URL'],'jobs')
                )
else:
    launcher = UrlLauncher(app.config['QUEUE_URL'])

# 
job_manager = JobManager(results_store, launcher)

app.notifier = Notifier(app.config, template_folder = 'templates')

# TODO this may be no longer necessary for local job launching
from app import views

@click.command('create-db')
@with_appcontext
def create_db():
    from app import db
    db.create_all()

# Tests the app excluding Selenium tests
@click.command('test')
@with_appcontext
def test_app():
    import os
    import pytest
    args = ['--rootdir', './tests', '-m',  'not ui']
    pytest.main(args)

@click.command('test-ui')
@with_appcontext
def test_app_ui():
    import pytest
    args = ['-k', 'ui']
    pytest.main(args)

app.cli.add_command(create_db)
app.cli.add_command(test_app)
app.cli.add_command(test_app_ui)