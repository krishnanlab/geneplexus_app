
from operator import truediv
import pytest, os, shlex
from mljob.job_manager import generate_job_id, JobManager, LocalLauncher, job_status_codes
import logging
logging.basicConfig()


@pytest.fixture()
def job_url():
    """ the goal is to have a url that the job can hit to report status for testing"""
    return("http://localhost:5000/jobs")

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


@pytest.fixture()
def existing_job_name(job_name, results_store, genelist, test_job_config):
    """do all needed to prep a folder for running a job against"""
    # this is mimicking job_manager too much -> refactor job prep into new function
    results_store.create(job_name)
    results_store.save_input_file(job_name, genelist)
    job_config_file = results_store.save_json_results(job_name, 'job_config', test_job_config)

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


class NullLauncher():
    def __init__(self,*args):
        pass
    def launch(self,job_name):
        return(200)

    
def test_job_manager_instantiate(results_store,genelist, test_job_config):
    # create a job manager composed of a storage and a launcher
    job_manager = JobManager(results_store, NullLauncher(), logging = logging )
    assert job_manager is not None
    assert str(type(job_manager )) == "<class 'mljob.job_manager.JobManager'>"


def test_job_manager_null_launch(results_store,genelist, test_job_config):
    job_manager = JobManager(results_store = results_store, launcher = NullLauncher(), logging = logging )
    resp = job_manager.launch(genes = genelist, job_config = test_job_config)
    assert resp == 200

    
def test_job_manager_api(results_store, existing_job_config):
    job_manager = JobManager(results_store, launcher = NullLauncher() , logging = logging)
    job_name = existing_job_config['jobname']
    # first check the job seems 'real'
    assert type(job_name) == type(" "), "job_name fixture is not a string"
    assert len(job_name) > 0, "job_name fixture is length 0"
    assert results_store.exists(job_name), "job fixture is supposed to exist, but doesn't"
    # now test the job_manager functions
    assert job_manager.job_exists(job_name) == True


def test_job_manager_local_launcher(data_path, results_store, test_job_config, genelist):
    
    launcher = LocalLauncher( data_path, results_store, logging = logging)
    job_manager = JobManager(results_store = results_store,launcher = launcher, logging = logging )

    job_name = test_job_config['jobname']

    resp = job_manager.launch( genes = genelist, job_config = test_job_config)
    # this will wait until the job is completed
    assert resp == 200
    assert results_store.has_results(job_name) == True 
    assert results_store.read_status(job_name) == job_status_codes[200]
    assert job_manager.job_completed(job_name) == True

    # basic tests that the job info is legit
    job_info = results_store.read_job_info(job_name)

    assert job_info is not None
    assert type(job_info) == type({})
    assert 'df_convert_out_subset_file' in list(job_info.keys())
    example_results_file_name = job_info.get("df_convert_out_subset_file")
    assert example_results_file_name is not None

    assert results_store.results_has_file(job_name, example_results_file_name) == True
    
    test_graph = results_store.read_graph_results(job_name)
    assert test_graph is not None
    assert len(test_graph ) > 0

    # test results listing
    jobnames = [job_name]
    joblist = results_store.job_info_list(jobnames)
    assert type(joblist) == type({})
    assert len(joblist) == 1
    job_info = joblist[job_name]
    assert job_info.get('has_results') == True

    