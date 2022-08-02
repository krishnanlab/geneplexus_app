
import pytest, os, shlex
from mljob.job_manager import generate_job_id, JobManager, LocalLauncher



@pytest.fixture()
def job_url():
    """ the goal is to have a url that the job can hit to report status for testing"""
    return("http://localhost:5000/jobs")

# @pytest.fixture()
# def dummy_job_launcher():
#     """ class to pass that known to work """

#     class NullLauncher():
#         def __init__(self,*args):
#             pass
#         def launch(self,job_config):
#             return('200')
    
#     nl = NullLauncher('x')
#     yield nl 


@pytest.fixture(scope='module')
def genelist():
    """ read in file that is in the test directory.  """
    input_file_path = 'tests/example_gene_file.txt'
    
    # fail the test suite if the file is not present
    if not os.path.exists(input_file_path):
        pytest.fail(f"can't find sample gene file {input_file_path}")

    with open(input_file_path, 'r') as f:
        data =  shlex.split(f.read())
    
    yield data

@pytest.fixture()
def existing_job_name(job_name, results_store, genelist):
    """do all needed to prep a folder for running a job against"""
    results_store.create(job_name)
    results_store.save_input_file(job_name, genelist)

    yield(job_name)

    if results_store and results_store.exists(job_name):
        print(f"deleting job store folder for {job_name}")
        results_store.delete(job_name)

@pytest.fixture()
def existing_job_config(existing_job_name, job_url):
    """ create configuration for a single job (params, etc)"""

    
    job_config = {
        'net_type'      : 'BioGRID',
        'features'      : "Embedding",
        'GSC'           : "DisGeNet",
        'jobname'       : existing_job_name, 
        'jobid'         : '',  # this is no longer used
        'job_url'       : job_url,
        'notifyaddress' :  'none@none.com'
    }

    yield job_config 


@pytest.fixture()
def test_job_config(job_name, job_url):
    """ create configuration for a single job (params, etc)"""

    
    job_config = {
        'net_type'      : 'BioGRID',
        'features'      : "Embedding",
        'GSC'           : "DisGeNet",
        'jobname'       : job_name, 
        'jobid'         : '',  # this is no longer used
        'job_url'       : job_url,
        'notifyaddress' :  'none@none.com'
    }

    yield job_config 


class NullLauncher():
    def __init__(self,*args):
        pass
    def launch(self,job_config):
        return('200')

def test_job_manager_instantiate(results_store):
    # create a job manager composed of a storage and a launcher
    job_manager = JobManager(results_store, NullLauncher() )
    assert job_manager is not None
    assert str(type(job_manager )) == "<class 'mljob.job_manager.JobManager'>"


def test_job_local_launcher(data_path, results_store, existing_job_config):
    # create launcher object
    launcher = LocalLauncher( data_path, results_store)

    assert launcher is not None
    assert str(type(launcher)) == "<class 'mljob.job_manager.LocalLauncher'>"

    response = launcher.launch(existing_job_config)
    assert response == '200'


def test_job_manager_null_launcher(results_store, test_job_config, genelist):
    
    job_manager = JobManager(results_store = results_store,launcher = NullLauncher())
    resp = job_manager.launch( genes = genelist, job_config = test_job_config)
    assert resp == '200'     

def test_job_manager_local_launcher(data_path, results_store, test_job_config, genelist):
    
    launcher = LocalLauncher( data_path, results_store)
    job_manager = JobManager(results_store = results_store,launcher = launcher )
    resp = job_manager.launch( genes = genelist, job_config = test_job_config)
    assert resp == '200'