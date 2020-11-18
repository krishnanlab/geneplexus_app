from flask import Flask
from config import ProdConfig, DevConfig
from dotenv import load_dotenv

load_dotenv('.flaskenv')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'something-no-one-would-guess'

if app.env == 'production':
    app.config.from_object(ProdConfig)
elif app.env == 'development':
    app.config.from_object(DevConfig)

from app import views, models