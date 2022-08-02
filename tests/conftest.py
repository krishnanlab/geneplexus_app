import multiprocessing
import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


from mljob.results_storage import ResultsFileStore


from dotenv import load_dotenv
load_dotenv('..')

from app import app as flask_app


@pytest.fixture(scope='session')
def app():
    # disabling multiprocessing for now as getting a RuntimeError: context has already been set when both UI and views testing is done
    # multiprocessing.set_start_method("fork") # This is because OSX and Windows uses spawn which isn't supported by pytest
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

@pytest.fixture(scope="session")
def data_path():
    dp = os.getenv('DATA_PATH')
    if not os.path.exists(dp):
        pytest.fail(f"can't find DATA_PATH {dp}, test stopped")
    else:
        yield dp

@pytest.fixture(scope='session')
def job_path():
    jp =  os.getenv('JOB_PATH')
    if not os.path.exists(jp):
        pytest.fail(f"can't find DATA_PATH {jp}, test stopped")
    else:
        yield jp


from mljob.job_manager import generate_job_id

@pytest.fixture()
def job_name(job_path):
    j = generate_job_id()
    print(f"using job id {j} for testing")
    yield j
    # sometimes a new folder is created... delete if so
    rs = ResultsFileStore(job_path)
    if rs and rs.results_folder_exists(j):
        print(f"deleting job store folder for {j}")
        rs.delete(j)
        # remove results store object
        del(rs)

@pytest.fixture()
def results_store(job_path):
    rs = ResultsFileStore(job_path)
    if not rs:
        pytest.fail(f"couldn't instantiate pytest with job_path {job_path}")
    yield rs