from app.db import db, login_manager
from flask_security import UserMixin, RoleMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm.collections import attribute_mapped_collection
from flask_security.models import fsqla_v3 as fsqla

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('user.id'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(db.UnicodeText)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    active = db.Column(db.Boolean())
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_users',
                         backref=db.backref('users', lazy='dynamic'))
    
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
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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

    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    jobname = db.Column(db.String(64), db.ForeignKey('jobs.jobid'))

    user = db.relationship('User', backref=db.backref('results', lazy=True))
    job = db.relationship('Job', backref=db.backref('results', lazy=True))

class FavoriteResult(db.Model):
    __tablename__ = 'favoriteresults'
    id = db.Column(db.Integer, primary_key=True)

    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resultid = db.Column(db.Integer, db.ForeignKey('results.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('favoriteresults', lazy=True))
    result = db.relationship('Result', backref=db.backref('favoriteresults', lazy=True))
    