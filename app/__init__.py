from flask import Flask
from config import ProdConfig, DevConfig
from dotenv import load_dotenv

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

from app import views, models