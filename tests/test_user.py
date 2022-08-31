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

def test_update_user(client, session):
    new_user = User('test', 'test', 'test@test.test', 'Test Name')
    session.add(new_user)
    session.commit()

    rv = login(client, 'test', 'test')

    data = {
        'username': 'test',
        'email': 'newemail@newemail.new',
        'fullname': 'New Person'
    }

    rv = client.post(url_for('edit_profile'), data=data, follow_redirects=True)
    print(new_user.email)
    print(new_user.name)
    assert new_user.email == 'newemail@newemail.new' and new_user.name == 'New Person'