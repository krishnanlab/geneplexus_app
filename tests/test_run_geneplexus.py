import pytest, os
import mljob.run_geneplexus
from mljob.results_storage import ResultsFileStore
from mljob.job_manager import generate_job_id

@pytest.fixture(scope="module")
def job_path():
    yield os.getenv('JOB_PATH')

@pytest.fixture(scope="module")
def data_path():
    yield os.getenv('DATA_PATH')


# just make one of these
@pytest.fixture(scope="module")
def results_store(job_path):
    rs = ResultsFileStore(job_path)
    if not rs:
        pytest.fail(f"couldn't instantiate pytest with job_path {job_path}")
    yield rs


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


def test_true(job_name):
    assert job_name is not None
    