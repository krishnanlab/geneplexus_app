from flask import Flask
from config import ProdConfig, DevConfig
from dotenv import load_dotenv
import logging

load_dotenv('.flaskenv')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'something-no-one-would-guess'

if app.env == 'production':
    app.config.from_object(ProdConfig)
elif app.env == 'development':
    app.config.from_object(DevConfig)

logging.basicConfig(filename=app.config.get('LOG_FILE'),level=logging.INFO)

from app import views, models