# unit tests for ResultStorage class

import pytest, os
from mljob.job_manager import generate_job_id
from mljob.results_storage import ResultsFileStore

"""
code to test the tests

job_path = os.getenv('JOB_PATH')
job_name = generate_job_id()
results_store(job_path)

"""
@pytest.fixture(scope='session')
def job_path():
    yield os.getenv('JOB_PATH')

@pytest.fixture()
def job_name():
    yield generate_job_id()

# just make one of these
@pytest.fixture(scope='session')
def results_store(job_path):
    yield ResultsFileStore(job_path)


def test_result_store_instantiate(results_store):
    # we do get a real object of the correct type
    assert results_store is not None
    assert str(type(results_store)) == "<class 'mljob.results_storage.ResultsFileStore'>"

    # this function should not fail, but without a valid job returns None
    assert results_store.results_folder('not a real job name') is None


