from app import login_manager, db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)

    def __repr__(self):
        return f'<User {self.name}; Email {self.email}>'
    
    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    jobid = db.Column(db.String(64), unique=True, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('jobs', lazy=True))