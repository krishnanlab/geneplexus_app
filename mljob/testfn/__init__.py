""" test function :  run a geneplexus job directly from http trigger
parameter is simply a job name. 
config is job path and data path 
job is run input read from, and output saved to store
returns http message and status code
"""
 
from run_geneplexus import run_and_save
from results_storage import ResultsFileStore

import logging
from slugify import slugify
from os import getenv, path
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """http job processing version, runs geneplexus from a URL. See queuejob and associate runjob for app versions"""
    
    logging.info(f"job processor triggered")

    def get_param(param_name):
        """ look into either body or query string for param, 
        return None if not found """

        param_value  = req.params.get(param_name)
        if not param_value:
            try:
                req_body = req.get_json()
            except ValueError:
                pass
            else:
                param_value  = req_body.get(param_value)
        return(param_value)
        
    #####  Configuration Validation
    jobs_path = getenv("JOBS_PATH")
    if not jobs_path:
        logging.error('JOBS_PATH is not set')
        return func.HttpResponse(
            "invalid server configuration",
            status_code=500
        )

    data_path = getenv("DATA_PATH")
    if not data_path or not path.exists(data_path):
        err_msg = 'data path not found'
        logging.error(err_msg)
        return func.HttpResponse(
            "invalid server configuration",
            status_code=500
        )


    ### param gathering 
    job_name = get_param('jobname')
    if not job_name:
        logging.error('400 job request incomplete (missing jobname')
        return func.HttpResponse(
            "jobname parameter required",
            status_code=400)

    try:
        # connect and confirm storage of job inputs and outputs
        results_store = ResultsFileStore(jobs_path)

        if not results_store.exists(job_name = job_name):
            logging.error(f"error : 404 : job not found {job_name}")
            return func.HttpResponse(
               "no job by that name found",
                status_code=404
        )


        ### read and check input file and params    
        if not results_store.has_input_file(job_name):
            err_msg = f"input file not found for job {job_name}"
            logging.error(err_msg)
            return func.HttpResponse(err_msg, status_code=400)

            
        job_config = results_store.read_config(job_name)
        if not job_config:
            err_msg = f"no configuration file found for job {job_name}"
            logging.error(err_msg)
            return func.HttpResponse(err_msg, status_code=400)

        net_type = job_config.get('net_type')
        features = job_config.get('features')
        GSC = job_config.get('GSC')

    except Exception as e:
        errmsg = f"Error with results store for job {job_name}, can't continue : {e}"
        logging.error(errmsg)
        return func.HttpResponse(err_msg, status_code=400)

    ### running.  
    try: 
        results_store.save_status(job_name, 'running')

        gp_ran = run_and_save(job_name, results_store, data_path, logging = logging, 
                    net_type=net_type, features=features, GSC=GSC)
        if  gp_ran:
            logging.info(f"job completed {job_name}")
            results_store.save_status(job_name, "complete") 
            return func.HttpResponse( "job completed", status_code=200) 
        else:
            logging.error(f"{job_name} failed to complete")
            results_store.save_status(job_name, "failed")
            return func.HttpResponse( "job run error", status_code=500) 
                

    except Exception as e:
        logging.error(f"{job_name} run error {e}")
        results_store.save_status(job_name, 'failed') 
        return func.HttpResponse( "job run error", status_code=500) 
    