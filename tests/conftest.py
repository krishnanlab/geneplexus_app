import multiprocessing
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from app import app as flask_app
from app import db as flask_db
from config import TestConfig

@pytest.fixture(scope='session')
def app():
    flask_app.config.from_object(TestConfig)
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield flask_app

@pytest.fixture(scope='session')
def db(request, app):
    def teardown():
        flask_db.drop_all()
    with app.app_context():
        flask_db.create_all()
    request.addfinalizer(teardown)
    return flask_db

@pytest.fixture(scope='function')
def session(db, request):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session

@pytest.fixture(scope='session')
def driver():
    options = Options()
    options.headless = True
    options.add_argument('--incognito')

    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(executable_path = s.path)
    # this errors in latest version of webdriver...
    # driver = webdriver.Chrome(service=s, options=options)
    yield driver
    driver.quit()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()