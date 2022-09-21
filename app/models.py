from app import login_manager, db
from flask_login import UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm.collections import attribute_mapped_collection

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    password = db.Column(db.String(128))
    security_token = db.Column(db.String(64), nullable=True)
    token_expiration = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, password, email, name):
        self.username = username
        self.email = email
        self.name = name
        self.password = generate_password_hash(password)
    
    def update_password(self, password):
        self.password = generate_password_hash(password)

    def __repr__(self):
        return f'<User {self.name}; Email {self.email}>'
    
    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)
    
class OAuth(OAuthConsumerMixin, db.Model):
    __table_args__ = (db.UniqueConstraint("provider", "provider_user_id"),)
    provider = db.Column(db.String(256), nullable=False)
    provider_user_id = db.Column(db.String(256), nullable=False)
    provider_user_login = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User,
        # This `backref` thing sets up an `oauth` property on the User model,
        # which is a dictionary of OAuth models associated with that user,
        # where the dictionary key is the OAuth provider name.
        backref=db.backref(
            "oauth",
            collection_class=attribute_mapped_collection("provider"),
            cascade="all, delete-orphan",
        ),
    )

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    jobid = db.Column(db.String(64), unique=True, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('jobs', lazy=True))

    def __init__(self, jobid, userid):
        self.jobid = jobid
        self.userid = userid

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    network = db.Column(db.String(256))
    feature = db.Column(db.String(256))
    negative = db.Column(db.String(256))
    p1 = db.Column(db.Float)
    p2 = db.Column(db.Float)
    p3 = db.Column(db.Float)
    public = db.Column(db.Boolean)
    description = db.Column(db.String(512), default='')

    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jobname = db.Column(db.String(64), db.ForeignKey('jobs.jobid'))

    user = db.relationship('User', backref=db.backref('results', lazy=True))
    job = db.relationship('Job', backref=db.backref('results', lazy=True))

class FavoriteResult(db.Model):
    __tablename__ = 'favoriteresults'
    id = db.Column(db.Integer, primary_key=True)

    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resultid = db.Column(db.Integer, db.ForeignKey('results.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('favoriteresults', lazy=True))
    result = db.relationship('Result', backref=db.backref('favoriteresults', lazy=True))
    