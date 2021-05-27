import requests
import json
import re, os
from slugify import slugify
from pandas import DataFrame
# import pandas as pd
from datetime import datetime

def path_friendly_jobname(jobname):
    """ job name must be useable to create file paths and other cloud resources, so remove unuesable or unicode characters"""
    #rules for conainters: The container name must contain no more than 63 characters and must match the regex '[a-z0-9]([-a-z0-9]*[a-z0-9])?' (e.g. 'my-name')."
    # this needs to be idempotent becuase we may call it on an already modified jobname to be safe

    # azure containers must have names matching regex '[a-z0-9]([-a-z0-9]*[a-z0-9])?' (e.g. 'my-name')."
    # this is  more restrictive that file paths.  
    # For slugify, the regex pattern is what to exclude, so it uses the negation operator ^
    # do two passes - one for slugify's chaacter conversion, and one to make it cloud friendly
    filefriendly_jobname = slugify(jobname.lower(), lowercase=True)
    
    cloud_container_exclude_pattern=r'[^a-z0-9]([^-a-z0-9]*[^a-z0-9])?'
    cloudfriendly_jobname = slugify(filefriendly_jobname, separator='-', regex_pattern=cloud_container_exclude_pattern)

    return(cloudfriendly_jobname)

def create_input_file_name(jobname):
    return('input_genes.txt')
    # jn = path_friendly_jobname(jobname)
    # return (f"{jn}_input.txt")

def create_results_file_name(jobname):
    return("results.html")
    # jn = path_friendly_jobname(jobname)
    # return (f"{jn}_results.html")

def create_json_file_name(jobname):
    jn = path_friendly_jobname(jobname)
    return(f"{jn}.json")


def job_json(job_config, app_config):
    """build the data payload for the http trigger """ 
    # TODO potentially remove all of this from this app
    app_config['CONTAINER_REGISTRY']="krishnanlabgeneplexusacr.azurecr.io"
    job_path=f"{app_config['BASE_CONTAINER_PATH']}/jobs/"
    jobname = path_friendly_jobname(job_config['jobname'])
    
    input_file_name = create_input_file_name(jobname)
    results_file_name = create_results_file_name(jobname)

#        "imageName": f"{acrname}.azurecr.io/{app_config['JOB_IMAGE_NAME']}:{app_config['JOB_IMAGE_TAG']}",
    # these values are set or can be discovered using commands in the CLI script. so perhaps they need to go 
    # direct into the ARM template directly (as params to the template), since they don't affect 
    # the app. 
    docker_image_config = {
        "imageName": f"{app_config['CONTAINER_REGISTRY_URL']}/{app_config['JOB_IMAGE_NAME']}:{app_config['JOB_IMAGE_TAG']}",
        "registry": {
            "server": app_config['CONTAINER_REGISTRY_URL'],
            "username": app_config['CONTAINER_REGISTRY_USER'],
            "password": app_config["CONTAINER_REGISTRY_PW"]
        }
    }

    # TODO remove all of this from this app, leave elsewhere
    volume_config = {
        "name": "geneplexusfiles",
                "mountPath": app_config['BASE_CONTAINER_PATH'],
                "readOnly": False,
                "shareName": "geneplexusfiles",
                "shareReadOnly": False,
                "storageAccountName": "geneplexusstorage",
                "storageAccountKey": app_config["STORAGE_ACCOUNT_KEY"]
    }

    envvars = {
        "FLASK_ENV": "development",
        "FLASK_DEBUG": True,
        "GP_NET_TYPE": job_config['net_type'],
        "GP_FEATURES": job_config['features'],
        "GP_GSC": job_config['GSC'],
        "JOBNAME": job_config['jobname'],
        "JOBID": job_config['jobid'],
        "DATA_PATH": f"{app_config['BASE_CONTAINER_PATH']}/data_backend2",
        "GENE_FILE": f"{job_path}/{job_config['jobname']}/{input_file_name}",
        "OUTPUT_FILE": f"{job_path}/{job_config['jobname']}/{results_file_name}",
        "JOB_PATH": job_path

    }

    # TODO get CPU and ram from job_config
    # TODO alter jog config, increase ram depending on network size
    #  
    job_data = {
        "aciName": "geneplexus-backend",
        "location": "centralus",
        "memoryInGB": 16,
        "cpu": 2,
        "volumeMount": volume_config,
        "image": docker_image_config,
        "envvars": envvars
    }

    return json.dumps(job_data)


def launch_job(genes, job_config, app_config):
    """prep job inputs for use with file paths, create JSON data, 
    save the input file (and json) to the share folder, 
    then send json to the logic app url that launches the job container
    
    This assumes the application has the following configured 
         app_config["STORAGE_ACCOUNT_KEY"] 
         app_config["CONTAINER_REGISTRY_PW"] 
         app_config["JOB_URL"] 
    """

    #TODO error checking : are all needed values in app_config?

    # prep all the filenames and paths
    jobname = path_friendly_jobname(job_config['jobname'])
    # jobid = job_config['jobid']
    input_file_name = create_input_file_name(jobname)
    json_file_name = create_json_file_name(jobname)
    local_job_folder = f"{app_config['JOB_PATH']}/{jobname}"


    input_file_path = f"{local_job_folder}/{input_file_name}"
    json_file_path = f"{local_job_folder}/{json_file_name}"

    #TODO use these tidied-up file names in the job_config
    job_data = job_json(job_config, app_config)
    
    # TODO wrap in try/catch
    # create new folder and write files into it
    if not os.path.isdir(local_job_folder):
        os.mkdir(local_job_folder)

    # write gene file
    with open(input_file_path, 'w') as f:
        f.writelines("%s\n" % gene for gene in genes)

    # only write the env vars from job data to storage
    # otherwise we are writing cloud-specific info (keys, etc) to storage that we don't need for job status
    # use this convoluted method json->dict->select one key->new dict->json
    job_vars = json.dumps({'envvars':json.loads(job_data)['envvars']})
    # write job params ( data sent to azure )
    with open(json_file_path, 'w') as f:
        f.write(job_vars)

    jsonHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    # launch! 
    response = requests.post(app_config['JOB_URL'],
                            data=job_data,
                            headers=jsonHeaders)

    print(f"Job data sent for {jobname}.  Status code: {response.status_code}")

    return response




def list_all_jobs(job_path): 
    """ given the path where jobs live, pull the list of all jobs """
    with os.scandir(job_path) as jobdir:
        joblist = [d.name for d in jobdir if d.is_dir() and not d.name.startswith('.')]

    return(joblist)    



def retrieve_job_folder(jobname, app_config):
    """ return the job folder, or empthy string if no job folder exists"""

    jobname = path_friendly_jobname(jobname)
    job_folder = os.path.join(app_config["JOB_PATH"], jobname)
    if os.path.isdir(job_folder):
        return(job_folder)
    else:
        return('')


def results_file_path(jobname, app_config):
    """construct the path to the job (for local/mounted file storage)"""
    jobname = path_friendly_jobname(jobname)
    jf = retrieve_job_folder(jobname, app_config)
    if jf:
        return(os.path.join(jf, create_results_file_name(jobname)))
    else:
        return('')


def check_results(jobname, app_config):
    """"  return T/F if there is a results file """
    fp = results_file_path(jobname, app_config)
    #  if results file exists and it's non-zero size, then true
    return( os.path.exists(fp) and os.path.getsize(fp) > 0) 


def retrieve_job_info(jobname, app_config):
    """ return a dict of job info for jobs table (no results) """
    jobname = path_friendly_jobname(jobname)

    # create default empty dict for consistent rows
    job_info = { 
        'jobname': jobname, 
        'is_job' : '',
        'submit_time' : '',
        'has_results' : '',
        'params' : '',
        'status' : ''
    }

    jf = retrieve_job_folder(jobname, app_config)
    if jf:
        job_info['is_job'] = True
        job_info['submit_time'] = datetime.fromtimestamp(os.path.getmtime(jf)).strftime("%Y-%m-%d %H:%M:%S")
        job_info['has_results'] = check_results(jobname, app_config)
        job_info['params']= retrieve_job_params(jobname, app_config)
        job_info['status']=retrieve_job_status(jobname, app_config)
    else:
        job_info['is_job'] = False
        job_info['status'] = 'NOT FOUND'

    return(job_info)
  
def job_info_list(jobnames, app_config):
    """for a list off jobnames, accumulate all the job_info"""
    jobinfolist = []
    if jobnames:
        jobinfolist = [retrieve_job_info(jobname, app_config) for jobname in jobnames]

    return(jobinfolist)
    
def retrieve_job_status(jobname, app_config, status_file_suffix = ".log", default_status = "SUBMITTED"):
    """ read the log file created by the job runner in the same folder as the results"""

    fp = results_file_path(jobname, app_config) + status_file_suffix
    last_line = default_status # this is the default
    # TODO , if the submit time is a long time ago, change status to NO ANSWER or similar

    if os.path.exists(fp):
        # try
        with open(fp, 'r') as f:
            last_line = f.readlines()[-1]
    
    return(last_line)


def retrieve_results(jobname, app_config):
    """ retrieve the results file (html) for a given job"""

    fp = results_file_path(jobname, app_config)
    
    # look for the path and file and if it's there, read it in
    if os.path.exists(fp):
        # try
        with open(fp) as f:
            content = f.read()
        
        return content

    else:
        return ''    


def retrieve_job_params(jobname, app_config):
    """construct the path to the job (for local/mounted file storage)"""    
    job_folder = retrieve_job_folder(jobname, app_config)
    if job_folder:
        params_file_path = os.path.join(job_folder, create_json_file_name(jobname))
    else:
        return('')

    if os.path.exists(params_file_path):
        with open(params_file_path) as f:
            content = f.read()

        params_vars = json.loads(content)

        return(params_vars['envvars'])
    else:
        return('')

def test_job(test_jobname="A_test_job!-A99", input_file='input_genes.txt'):
    from app import app
    # in calling function, Assign variables to navbar input selections
    # job_config['net_type']  # = request.form['network']
    # job_config['features']  # = request.form['feature']
    # job_config['GSC']  # = request.form['negativeclass']
    # job_config['jobname'] #= request.form['jobname']

    job_config = {}
    job_config['net_type'] = "BioGRID"
    job_config['features'] = "Embedding"
    job_config['GSC'] = "DisGeNet"
    job_config['jobname'] = test_jobname
    job_config['jobid'] = "A99"
    
    # there should be a sample input file checked into git
    with open(input_file, 'r') as f:
        genes = f.read()

    print("launching")
    response = launch_job(genes, job_config, app.config)
    print("response = ", response)
