""" runjob azure function :  run a geneplexus job from queue
    valid data keys sent are 'net_type', 'features', 'GSC','jobname','job_url'
        """
# runjob.__init__.py 
# read jobname from queue and run. 

from run_geneplexus import run_and_save
from results_storage import ResultsFileStore
import logging
from os import getenv, path
import requests, json
from urllib.parse import urlparse
from pathlib import Path
from job_manager import job_status_codes

import azure.functions as func

def main(msg: func.QueueMessage) -> None:
    """given a jobname, 
    initialize the results store
    read the job info and input from the store, 
    execute Geneplexus, 
    write output to the store, and 
    hit the callback URL with jobname and status"""

    logging.info(f"job runner triggered by Queue message")

    #####  Configuration Validation
    jobs_path = getenv("JOBS_PATH")
    if not jobs_path:
        logging.error('JOBS_PATH is not set')
        return

    data_path = getenv("DATA_PATH")
    if not data_path or not path.exists(data_path):
        err_msg = 'data path not found'
        logging.error(err_msg)

    ### param gathering and validation
    try:
        jobname = msg.get_body().decode('utf-8')
        logging.info(f"retrieved job from queue:  {jobname}")
    except Exception as e:
        logging.error(f"error retrieving jobname from queue msg: {e}")
        return
        
    try:
        # connect and confirm storage of job inputs and outputs
        results_store = ResultsFileStore(jobs_path)

        if not results_store.exists(job_name = jobname):
            logging.error(f"error : 404 : job not found {jobname}")
            return


        ### read and check input file and params    
        if not results_store.has_input_file(jobname):
            err_msg = f"input file not found for job {jobname}"
            logging.error(err_msg)
            return
            
        job_config = results_store.read_config(jobname)
        if not job_config:
            err_msg = f"no configuration file found for job {jobname}"
            logging.error(err_msg)
            return

        net_type = job_config.get('net_type')
        features = job_config.get('features')
        GSC = job_config.get('GSC')

    except Exception as e:
        errmsg = f"Error with results store for job {jobname}, can't continue : {e}"
        logging.error(errmsg)
        return

    
    ### running.  
    try: 
        gp_ran = run_and_save(jobname, results_store, data_path, logging = logging, 
                    net_type=net_type, features=features, GSC=GSC)
        if  gp_ran:
            logging.info(f"job completed {jobname}")
            results_store.save_status(jobname, job_status_codes[200]) 
            # SET STATUS     
        else:
            logging.error(f"{jobname} failed to complete")
            results_store.save_status(jobname, job_status_codes[500]) 

    except Exception as e:
        logging.error(f"{jobname} run error {e}")
        results_store.save_status(jobname, job_status_codes[500]) 
        

    # job is complete.  Post to the app callback URL if one was set in config
    callback_url = getenv("CALLBACK_URL")
    # check if a url was actually configured
    if not callback_url: 
        logging.error(f"{jobname} configuration for CALLBACK_URL is not set, can't post status")
        return

    # check that the url in the configuration is a value http(s) url for defensive security
    try:
        parsed_url = urlparse(callback_url)
        if parsed_url.scheme != 'http' and parsed_url.scheme != 'https': 
            raise ValueError("URL must be http or https")
    
    except ValueError as e:
        # if the configuration url is not valid or is not http or https it will get here
        logging.error(f"{jobname} configuration for CALLBACK_URL is not valid: {e}")
        return


    # url is present and valid
    # add the jobname to the path.   this assumes the job name does not contain any url-like string
    # the app uses slugify to remove slashes and periods 
    # join main website url with job name and guarantee exactly one slash between 
    # job name must _not_ start with a slash
    
    callback_url = Path(callback_url,jobname)
    
    json_data = json.dumps({'status' : results_store.read_status(jobname) })
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    
    response = requests.post(callback_url, json=json_data, headers = headers )

    
    logging.info(f"call back response for job {jobname} : {response}")

    