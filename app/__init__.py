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
# TODO actually create a logger
# logger = logging.getLogger('app')

# job_folder configuration
job_folder = Path(app.config.get('JOB_PATH'))
if not job_folder.exists():
    job_folder.mkdir()

app.notifier = Notifier(app.config, template_folder = 'templates')

# replace old code with new import
from mljob import geneplexus_previous
geneplexus_previous.set_config(app.config)

from app import views

@click.command('create-db')
@with_appcontext
def create_db():
    from app import db
    db.create_all()

app.cli.add_command(create_db)