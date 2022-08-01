# unit tests for ResultStorage class

from multiprocessing import dummy
import pytest, os
from mljob.job_manager import generate_job_id
from mljob.results_storage import ResultsFileStore

"""
# some code to test the tests in the python cli
from dotenv  import load_dotenv; load_dotenv()
job_path = os.getenv('JOB_PATH')
job_name = generate_job_id()
results_store = ResultsFileStore(job_path)
type(results_store)
rs = results_store.create(job_name)
print(results_store.results_folder_exists(job_name))
type(rs)

"""
@pytest.fixture(scope='session')
def job_path():
    yield os.getenv('JOB_PATH')

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

# just make one of these
@pytest.fixture()
def results_store(job_path):
    rs = ResultsFileStore(job_path)
    if not rs:
        pytest.fail(f"couldn't instantiate pytest with job_path {job_path}")
    yield rs

def test_results_store_requires_valid_jobpath():
    """ check that an exception is raised if invalid job path sent"""
    with pytest.raises(Exception) as e_info:
       rs = ResultsFileStore("not/a/real/path")

def test_results_store_instantiate(results_store):
    """ can results_store object be created and is valid"""
    # now use the fixture
    assert results_store is not None
    assert str(type(results_store)) == "<class 'mljob.results_storage.ResultsFileStore'>"
    # this function should not fail, but without a valid job returns None
    assert 'notarealjobname' in results_store.results_folder('notarealjobname') 
    assert results_store.results_folder_exists('notarealjobname') is False


def test_results_store_create(results_store, job_name):
    rs_created = results_store.create(job_name)
    assert rs_created == True
    assert results_store.results_folder(job_name) is not None
    assert results_store.results_folder_exists(job_name) is True


def test_results_store_save(results_store, job_name):
    """ test if can save something and then the file is there"""
    rs_created = results_store.create(job_name)
    if rs_created:
        with open('tests/example_gene_file.txt') as f:
            genes = f.read()

        fname = results_store.save_txt_results(job_name, 'inputfile.txt', genes)
        expected_name = results_store.construct_results_filename(job_name, 'inputfile.txt')
        assert fname == expected_name
        assert results_store.results_has_file(job_name, expected_name)
    else:
        pytest.fail("couldn't create results store")

def test_results_store_delete(results_store, job_name):
    """ test if can delete a job folder in the store"""
    rs_created = results_store.create(job_name)
    if rs_created:
        results_store.delete(job_name)
    else:
        pytest.fail("couldn't create results store")

def test_results_store_genesets(results_store, job_name):
    """test if can read/write input file consistently"""
    rs_created = results_store.create(job_name)

    dummy_data = ['a', 'b', 'c']

    input_file_name = results_store.standard_input_file_name(job_name)
    assert type(input_file_name ) == type("string")
    assert job_name in input_file_name
    # not making any assertions about the actual template of the name

    if rs_created:
        results_store.save_input_file(job_name, dummy_data)
        assert results_store.results_has_file(job_name, input_file_name), "standard input file not found"

        check_data = results_store.read_input_file(job_name)
        assert dummy_data == check_data

    else:
        pytest.fail("couldn't create results store for input file test")


def test_results_status(results_store, job_name):

    test_status_msg = "test job"
    rs_created = results_store.create(job_name)
    if rs_created:
        status_file_name = results_store.save_status(job_name, test_status_msg)
        assert results_store.results_has_file(job_name, status_file_name), "status file not found"

        status_as_read = results_store.read_status(job_name)
        assert test_status_msg == status_as_read

    
    
#TODO write test that takes some existing output from a job, and saves it.   redundant with job running tests