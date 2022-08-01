
import pytest, os, shlex
from mljob.results_storage import ResultsFileStore
from mljob.job_manager import generate_job_id, JobManager

# these are duplicated in test_results_store so could be moved to conf test

@pytest.fixture(scope='module')
def job_path():
    yield os.getenv('JOB_PATH')

# just make one of these
@pytest.fixture()
def results_store(job_path):
    rs = ResultsFileStore(job_path)
    if not rs:
        pytest.fail(f"couldn't instantiate pytest with job_path {job_path}")
    yield rs


@pytest.fixture()
def existing_job_name(job_name, results_store):
    job_name = generate_job_id()
    results_store.create(job_name)
    rs = ResultsFileStore(job_path)
    if rs and rs.results_folder_exists(j):
        print(f"deleting job store folder for {j}")
        rs.delete(j)


@pytest.fixture()
def job_id(job_path):
    j = generate_job_id()
    print(f"using job id {j} for testing")
    yield j


@pytest.fixture()
def job_url():
    """ the goal is to have a url that the job can hit to report status for testing"""
    return("")

@pytest.fixture()
def dummy_job_launcher():
    """ function to pass """
    def null_job_launcher(*args):
        return('202')

    yield null_job_launcher

@pytest.fixture()
def test_job_config(job_id, job_url):
    job_config = {}
    job_config['features'] = "Embedding"
    job_config['GSC'] = "DisGeNet"
    job_config['jobname'] = f"testjob_{job_id}" 
    job_config['jobid'] = job_id
    job_config['job_url'] = job_url
    job_config['notifyaddress'] =  ''

    yield job_config 

@pytest.fixture(scope='session')
def genelist():
    """ read in file that is in the test directory.  """
    input_file_path = 'tests/example_gene_file.txt'
    
    # fail the test suite if the file is not present
    if not os.path.exists(input_file_path):
        pytest.fail(f"can't find sample gene file {input_file_path}")

    with open(input_file_path, 'r') as f:
        data =  shlex.split(f.read())
    
    yield data



def test_job_manager_instantiate(results_store, dummy_job_launcher):
    # create a job manager composed of a storage and a launcher
    job_manager = JobManager(results_store, dummy_job_launcher)

    assert job_manager is not None
    assert str(type(job_manager )) == "<class 'mljob.job_manager.JobManager'>"

def test_job_manager_launch(results_store, dummy_job_launcher,test_job_config, genelist):

    job_manager = JobManager(results_store, dummy_job_launcher)

    response = job_manager.launch( genes = genelist, job_config = test_job_config)
    
        
