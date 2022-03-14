import multiprocessing

import pytest

from app import app as flask_app

@pytest.fixture
def chrome_options(request, chrome_options):
    #chrome_options.headless = True
    chrome_options.add_argument('--incognito')
    return chrome_options

@pytest.fixture(scope='session')
def app():
    multiprocessing.set_start_method("fork")
    flask_app.config.update({
        'TESTING': True
    })
    yield flask_app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()