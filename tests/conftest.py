import multiprocessing
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from dotenv import load_dotenv
load_dotenv('..')

from app import app as flask_app


@pytest.fixture(scope='session')
def app():
    multiprocessing.set_start_method("fork") # This is because OSX and Windows uses spawn which isn't supported by pytest
    flask_app.config.update({
        'TESTING': True
    })
    yield flask_app

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