from flask import url_for
import pytest
from app.models import *

def test_add_user(session):
    new_user = User('test', 'test', 'test@test.test', 'Test Name')
    session.add(new_user)
    session.commit()
    result_test = User.query.all()
    assert len(result_test) == 1

def test_add_job(session):
    new_user = User('test', 'test', 'test@test.test', 'Test Name')
    session.add(new_user)
    session.commit()

    new_job = Job('testjob', new_user.id)
    session.add(new_job)
    session.commit()

    result_test = Job.query.all()
    assert len(result_test) == 1

def test_add_result(session):
    new_user = User('test', 'test', 'test@test.test', 'Test Name')
    session.add(new_user)
    session.commit()

    new_job = Job('testjob', new_user.id)
    session.add(new_job)
    session.commit()

    new_result = Result(
        network='BioGrid',
        feature='Embedding',
        negative='GO',
        p1=0.5,
        p2=0.5,
        p3=0.5,
        public=True,
        description='This is a description',
        userid=new_user.id,
        jobname='testjob'
    )
    session.add(new_result)
    session.commit()

    result_test = Result.query.all()
    assert len(result_test) == 1

