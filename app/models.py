
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

from app import login_manager
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()

class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    email = Column(String(64), unique=True, nullable=False)
    password = Column(String(64))

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)

    def __repr__(self):
        return f'<User {self.name}; Email {self.email}>'
    
    def verify_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    jobid = Column(String(64), unique=True, nullable=False)
    userid = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship('User')