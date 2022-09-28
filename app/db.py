from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flask_security.datastore import SQLAlchemySessionUserDatastore

from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()

#user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

login_manager = LoginManager()

def init_db():
    import app.models
    db.create_all()