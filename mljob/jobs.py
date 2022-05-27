import requests
import json
import os, sys, pathlib #, re, errno
from slugify import slugify
from datetime import datetime
from mljob.geneplexus import run_and_render
from mljob.model_output import read_output

from random import choices as random_choices
from string import ascii_lowercase, digits

# job status codes is a simple dictionary mirroring a small subset of http status codes
# these are status codes sent from the api that creates the job, or via the job itself. 
# some job status codes are the results of status codes from http trigger of the job launcher (auzre logic app in our case)
# note that 'timeout' is not 'gateway timeout'
job_status_codes = {200:"Completed", 201:"Created", 202:"Accepted", 404:"Not Found", 500:"Internal Server Error", 504:"Timeout"}

jobs_status_descriptions = { 200:"Job completed successfully", 
    201:"Job was created and may or may not be running", 
    202:"Job was accepted and is being created", 
    404:"There is no job with that specification on this server (ID)", 
    500:"There was a problem with the job creation or a run-time error",
    504:"Timeout.  There has been no status updates from the job within the expected time, assumed error"
    }

# standardized file name for reading /wrwiting status codes in job folder
job_status_filename = "JOBSTATUS"

def generate_job_id():
    eight_char_rand_id = ''.join(random_choices(population = ascii_lowercase + digits, k=8))
    return(eight_char_rand_id)

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

def valid_results_filename(possible_file_name):
    """convert user input into value OS filename, strip out most punctuation and spacing, preserve case. 
    The goal is to reduce risk of security problems from user input but allow what should be a valid
    results file name.  This does not limit to what we may know as valid file names"""

    file_regex_pattern = r'[^-A-Za-z0-9_\.]+'
    slugified_file_name = slugify(possible_file_name, lowercase=False,regex_pattern=file_regex_pattern)
    return(slugified_file_name)


def create_job_folder_name(job_config, app_config):
    """create standardized job folder path given application configuration"""
    local_job_folder = f"{app_config['JOB_PATH']}/{job_config['jobname']}"
    return(local_job_folder)


def create_input_file_name(jobname):
    return('input_genes.txt')
    # jn = path_friendly_jobname(jobname)
    # return (f"{jn}_input.txt")

def create_results_file_name(jobname):
    return("job_info.json")
    # jn = path_friendly_jobname(jobname)
    # return (f"{jn}_results.html")

def create_json_file_name(jobname):
    jn = path_friendly_jobname(jobname)
    return(f"{jn}.json")

def create_notifyaddress_file_name(jobname):
    """standardized notifier file naming"""
    return('NOTIFY')

def save_notifyaddress(job_config, app_config):
    """create a new file in the job folder to hold the notifier email address.  
    this is not going into the job info json file for now because we also send that to the 
    job runner, and that does not need this address"""
    job_dir = create_job_folder_name(job_config, app_config)
    notifyaddress_file = os.path.join(job_dir, create_notifyaddress_file_name(job_config['jobname']))
    with open(notifyaddress_file, 'w') as nf:
        nf.write(job_config['notifyaddress'])

    return(notifyaddress_file)


def get_notifyaddress(jobname, app_config):
    """ retrieve the email address that was notified for this job, if any. Return the email address"""

    notifyaddress = None

    if job_exists(jobname, app_config):

        jf = retrieve_job_folder(jobname, app_config)    
        notifyaddress_file = os.path.join(jf, create_notifyaddress_file_name(jobname))

        try:
            notifyaddress = pathlib.Path(notifyaddress_file).read_text()
        except:
            print(f"File with notifier info {notifyaddress_file} not found or readable", file=sys.stderr)

    return(notifyaddress)


def job_json(job_config, app_config):
    """build the data payload for the http trigger """ 
    # TODO remove the hard-coded "jobs" folder here and set as config value
    # the job folder ('jobs') must be in sync in the app and the job-runner container setting
    job_path=f"{app_config['JOB_CONTAINER_FILE_MOUNT']}/jobs/"
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

    # TODO remove all of this config from this app?  
    # most does not change from job-to-job, so set it when creating the logic app
    volume_config = {
        "name": "geneplexusfiles",
                "mountPath": app_config['JOB_CONTAINER_FILE_MOUNT'],
                "readOnly": False,
                "shareName": app_config["STORAGE_SHARE_NAME"],
                "shareReadOnly": False,
                "storageAccountName": app_config["STORAGE_ACCOUNT_NAME"],
                "storageAccountKey": app_config["STORAGE_ACCOUNT_KEY"]
    }

    # TODO see above, set most of this when creating the logic app
    # TODO remove the hard-coded data folder, and set this as an env var
    envvars = {
        "FLASK_ENV": "development",
        "FLASK_DEBUG": True,
        "GP_NET_TYPE": job_config['net_type'],
        "GP_FEATURES": job_config['features'],
        "GP_GSC": job_config['GSC'],
        "JOBNAME": job_config['jobname'],
        "JOBID": job_config['jobid'],
        "DATA_PATH": f"{app_config['JOB_CONTAINER_FILE_MOUNT']}/data_backend2/",
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

    # save notifier address 
    notifier_file_name = save_notifyaddress(job_config, app_config)

    if app_config['RUN_LOCAL']:
        print("running job locally (may take a while")
        run_and_render(genes, net_type=job_config['net_type'], features=job_config['features'], GSC=job_config['GSC'], jobname=jobname, output_path=local_job_folder)
        response = "200"

    else:
        jsonHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        # launch! 
        response = requests.post(app_config['JOB_URL'],
                            data=job_data,
                            headers=jsonHeaders)

        print(f"Job data sent for {jobname}.  Status code: {response.status_code}", file=sys.stderr)

    return response




def list_all_jobs(job_path): 
    """ given the path where jobs live, pull the list of all jobs """
    with os.scandir(job_path) as jobdir:
        joblist = [d.name for d in jobdir if d.is_dir() and not d.name.startswith('.')]

    return(joblist)    



def retrieve_job_folder(jobname, app_config):
    """ return the job folder, or empty string if no job folder exists"""

    jobname = path_friendly_jobname(jobname)
    job_folder = os.path.join(app_config["JOB_PATH"], jobname)
    if os.path.isdir(job_folder):
        return(job_folder)
    else:
        return('')


def job_exists(jobname, app_config):
    jobname = path_friendly_jobname(jobname)
    jf = retrieve_job_folder(jobname, app_config)
    if jf:
        return(True)
    else:
        return(False) 

def results_file_path(jobname, app_config, results_file = None):
    """construct the path to the job (for local/mounted file storage)"""
    
    jobname = path_friendly_jobname(jobname)

    # use the default name if none given 
    if not ( results_file) :
        results_file = create_results_file_name(jobname)

    jf = retrieve_job_folder(jobname, app_config)
    if jf:
        return(os.path.join(jf, results_file))
    else:
        return('')


def results_file_dir(jobname, app_config, data_file_name = None):
    """return to flask the absolute patah to a data file to be returned for download, 
    or nothing if neigher the job path exists, or the file does not exist in the job path
    (this is different than retrieve_job_folder)
    parameters
        jobname = id of job
        app_config config dictionary used to find the job path
        data_file_name  output file to look for
    returns
        jf directory where files live
        data_file_name, same data file name (santized)

    """
    # sanitize the input
    # use the default name if none given 
    if not ( data_file_name) :
        data_file_name = create_results_file_name(jobname)
    else:
        data_file_name = valid_results_filename(data_file_name)

    # get the path this job
    jf = retrieve_job_folder(jobname, app_config) # get path if job exists, or return ''

    if jf:
        data_file_path = os.path.join(jf, data_file_name)
        if os.path.exists(data_file_path):
            return(jf)
        
    return(None)



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
        'is_job' : False,
        'submit_time' : '',
        'has_results' : False,
        'params' : '',
        'status' : 404,
        'notifyaddress' : '',
        'job_url' : ''
    }

    jf = retrieve_job_folder(jobname, app_config)
    if jf:
        job_info['is_job'] = True
        job_info['submit_time'] = datetime.fromtimestamp(os.path.getmtime(jf)).strftime("%Y-%m-%d %H:%M:%S")
        job_info['has_results'] = check_results(jobname, app_config)
        job_info['status'] = retrieve_job_status(jobname, app_config)
        job_info['notifyaddress'] = get_notifyaddress(jobname, app_config)
        job_info['job_url'] = '' # this is a placeholder until I find non-clunky way to get use url_for without importing all of flask

        # now a hack to make the params fields consistent with 
        # how it's constructed in app.views.launch_job() and how it's saved to disk in jobs.launch_job()
        # TODO : move the code that creates a job_config dictionary and file into jobs.py from views.py

        job_params = retrieve_job_params(jobname, app_config)
        
        job_info['params'] = job_params  # save the whole thing just because
        job_info['net_type'] = job_params.get('GP_NET_TYPE')
        job_info['features'] = job_params.get('GP_FEATURES')
        job_info['GSC'] = job_params.get('GP_GSC')
        job_info['jobid'] = job_params.get('JOBID')

    return(job_info)
  
def job_info_list(jobnames, app_config):
    """for a list off jobnames, accumulate all the job_info"""
    jobinfolist = []
    if jobnames:
        jobinfolist = [retrieve_job_info(jobname, app_config) for jobname in jobnames]

    return(jobinfolist)
    
def retrieve_job_status(jobname, app_config, status_file_suffix = ".log", default_status = "SUBMITTED"):
    """ DEPRECATED for simpler version below.   read the log file created by the job runner in the same folder as the results"""

    fp = results_file_path(jobname, app_config) + status_file_suffix
    last_line = default_status # this is the default
    # TODO , if the submit time is a long time ago, change status to NO ANSWER or similar

    if os.path.exists(fp):
        # try
        with open(fp, 'r') as f:
            log_contents = f.readlines()
            # sometimes the file is not read (may be blocked?), so don't try to read it...
            if log_contents:
                last_line = log_contents[-1]
    
    return(last_line)

def set_job_status(jobname, job_status, app_config):
    """set a single file JOBSTATUS in job folder"""
    jf = retrieve_job_folder(jobname, app_config)
    if jf and job_status in job_status_codes:

        job_status_file = os.join(jf, job_status_filename)

        with open(job_status_file , 'w') as f:
            f.write(job_status)
        return(job_status_file)
    else:
        return(None)

def get_job_status(jobname,app_config):
    """ if the job exists, read the job """
    jf = retrieve_job_folder(jobname, app_config)
    if jf:
        job_status_file = os.join(jf, job_status_filename)
        if os.path.exists(job_status_file):
            with open(job_status_file , 'r') as f:
                job_status = f.read()
                try:
                    job_status = int(job_status)
                except:
                    print("error  job status file contents not numeric", file = sys.stderr)
        else:
            job_status = 0
        
    else:
        job_status = 404
  
    return(job_status)


# move to mljob/model_output.py
def retrieve_results(jobname, app_config):
    """ retrieve the results file (html) for a given job"""

    fp = results_file_path(jobname, app_config, 'results.html')
    
    print(f"looking up {fp}", file=sys.stderr)
    # look for the path and file and if it's there, read it in
    if fp and os.path.exists(fp):
        # try
        with open(fp) as f:
            content = f.read()
        
        return content

    else:
        return ''    

# coordinate/replace with mljob/model_output.py:read_df_output() method
def retrieve_results_data(jobname, app_config, data_file_name):
    """get any one of several of the results data files (TSV, JSON, etc)
    This does not check if the file name is one of the 'approved' file names to give 
    flexibility to the job runner during development"""

    data_file_name = valid_results_filename(data_file_name)

    # TODO define standard filenames for various results types and vet data file name as security precaution


    jf = retrieve_job_folder(jobname, app_config) # get path if job exists, or return ''

    # if the path, and the file both exists, read it and return the contents
    if jf:
        data_file_path = os.path.join(jf, data_file_name)
        if os.path.exists(data_file_path):
            try:
                with open(data_file_path) as f:
                    content = f.read()
            except OSError:
                print(f"OS error trying to read {data_file_path}",file=sys.stderr)
            except Exception as err:
                print(f"Unexpected error opening {data_file_path} is",repr(err),file=sys.stderr)
            else:
                return(content)
    
    # otherwise return none
    return(None)



# coordinate/replace with mljob/model_output.py:read_job_info() method
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

def retrieve_job_outputs(jobname, app_config):
    """ get everything from a job for rendering the job output/results page"""
    job_folder = retrieve_job_folder(jobname, app_config)  # is this same as output path, or is there another method for just output path
    output_path = job_folder  # these are the same thing in the two module

    return(read_output(output_path, jobname))
    

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

    print("launching",file=sys.stderr)
    response = launch_job(genes, job_config, app.config)
    print("response = ", response,file=sys.stderr) 

