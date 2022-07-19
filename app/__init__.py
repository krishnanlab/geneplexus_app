from flask import Flask
from flask.cli import with_appcontext
from flask_login import LoginManager
import click
from config import ProdConfig, DevConfig
from dotenv import load_dotenv
import logging
from pathlib import Path
from mljob.notifier import Notifier
from app.db import db_session

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

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

login_manager = LoginManager(app)

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

from mljob import geneplexus
geneplexus.set_config(app.config)

from app import views

@click.command('create_db', help = 'Create database from models.py.')
@click.option('--uri', default='sqlite:///test.db')
@with_appcontext
def create_db(uri):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.ext.declarative import declarative_base
    import app.models as models
    print('Creating initial DB tables at {}'.format(uri))
    engine = create_engine(uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                            autoflush=False,
                                            bind=engine))
    models.Base.metadata.create_all(bind=engine)

app.cli.add_command(create_db)