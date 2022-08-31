from flask import url_for
import pytest
from app.models import *

def login(client, username, password):
    return client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)

def test_login(client, session):
    new_user = User('test', 'test', 'test@test.test', 'Test Name')
    session.add(new_user)
    session.commit()

    rv = login(client, 'test', 'test')

    assert b'Username and password combination did not match' not in rv.data

def test_public_accessibility(client, session, job_name, results_store):
    private_user = User('secret', 'secret', '', '')
    session.add(private_user)
    session.commit()

    private_job = Job(job_name, private_user.id)
    session.add(private_job)
    session.commit()

    private_result = Result(
        network='BioGrid',
        feature='Embedding',
        negative='GO',
        p1=0.5,
        p2=0.5,
        p3=0.5,
        public=True,
        description='This is a description',
        userid=private_user.id,
        jobname=private_job.jobid
    )
    session.add(private_result)
    session.commit()

    created = results_store.create(job_name)
    if not created:
        pytest.fail("couldn't create results store")

    rv = client.get(url_for('job',jobname=private_job.jobid), follow_redirects=True)
    assert b'GenePlexus | Job' in rv.data

    private_result.public = False
    session.commit()

    rv = client.get(url_for('job',jobname=private_job.jobid), follow_redirects=True)
    assert b'either does not exist or is private' in rv.data

    rv = login(client, 'secret', 'secret')
    assert b'Username and password combination did not match' not in rv.data

    rv = client.get(url_for('job',jobname=private_job.jobid), follow_redirects=True)
    assert b'GenePlexus | Job' in rv.data

def test_public_visibility(client, session, job_name, results_store):
    private_user = User('secret', 'secret', '', '')
    session.add(private_user)
    session.commit()

    private_job = Job(job_name, private_user.id)
    session.add(private_job)
    session.commit()

    private_result = Result(
        network='BioGrid',
        feature='Embedding',
        negative='GO',
        p1=0.5,
        p2=0.5,
        p3=0.5,
        public=True,
        description='This is a description',
        userid=private_user.id,
        jobname=private_job.jobid
    )
    session.add(private_result)
    session.commit()

    created = results_store.create(job_name)
    if not created:
        pytest.fail("couldn't create results store")

    rv = client.get(url_for('public_results'))
    assert private_job.jobid.encode('utf-8') in rv.data

    private_result.public = False
    session.commit()

    rv = client.get(url_for('public_results'))
    assert private_job.jobid.encode('utf-8') not in rv.data