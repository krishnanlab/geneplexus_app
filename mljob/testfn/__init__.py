""" test function :  run a geneplexus job directly from http trigger
valid data keys sent are
            'net_type', 
            'features', 
            'GSC',
            'jobname',
            'jobid',
            'job_url'
            
"""
 
from run_geneplexus import run_and_save
from results_storage import ResultsFileStore

import logging
from slugify import slugify
from os import getenv, path
import azure.functions as func


data_keys = {'net_type', 
            'features', 
            'GSC',
            'jobname',
            'jobid',
            'job_url' }



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

    results_store = ResultsFileStore(jobs_path)

    if not results_store.exists(job_name = job_name):
        logging.error(f"error : 404 : job not found {job_name}")
        return func.HttpResponse(
            "no job by that name found",
            status_code=404
        )
        
    if not results_store.has_input_file(job_name):
        err_msg = 'no input gene file in job folder'
        return func.HttpResponse(f"input file not found for job {job_name}", status_code=400)

    net_type = get_param('net_type')
    features = get_param('features')
    GSC = get_param('GSC')

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
    
