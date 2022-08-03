""" runjob azure function :  run a geneplexus job from queue
    valid data keys sent are 'net_type', 'features', 'GSC','jobname','job_url'
        """
# runjob.__init__.py 
# read job_name from queue and run. 

from run_geneplexus import run_and_save
from results_storage import ResultsFileStore
import logging
from os import getenv, path
import azure.functions as func

def main(msg: func.QueueMessage) -> None:
    
    logging.info(f"job runner triggered by Queue message")

    try:
        job_name = msg.get_body().decode('utf-8')
        logging.info(f"retrieved job from queue:  {job_name}")
    except Exception as e:
        logging.error(f"error retrieving job_name from queue msg: {e}")
        return


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
    job_name = get_param('jobname')
    if not job_name:
        logging.error('400 job request incomplete (missing jobname')
        return

    try:
        # connect and confirm storage of job inputs and outputs
        results_store = ResultsFileStore(jobs_path)

        if not results_store.exists(job_name = job_name):
            logging.error(f"error : 404 : job not found {job_name}")
            return


        ### read and check input file and params    
        if not results_store.has_input_file(job_name):
            err_msg = f"input file not found for job {job_name}"
            logging.error(err_msg)
            return
            
        job_config = results_store.read_config(job_name)
        if not job_config:
            err_msg = f"no configuration file found for job {job_name}"
            logging.error(err_msg)
            return

        net_type = job_config.get('net_type')
        features = job_config.get('features')
        GSC = job_config.get('GSC')

    except Exception as e:
        errmsg = f"Error with results store for job {job_name}, can't continue : {e}"
        logging.error(errmsg)
        return

    
    ### running.  
    try: 
        results_store.save_status(job_name, 'running')

        gp_ran = run_and_save(job_name, results_store, data_path, logging = logging, 
                    net_type=net_type, features=features, GSC=GSC)
        if  gp_ran:
            logging.info(f"job completed {job_name}")
            results_store.save_status(job_name, "complete") 
            return 
        else:
            logging.error(f"{job_name} failed to complete")
            results_store.save_status(job_name, "failed")
            return
                

    except Exception as e:
        logging.error(f"{job_name} run error {e}")
        results_store.save_status(job_name, 'failed') 
        return
