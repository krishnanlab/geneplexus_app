import logging
import requests
import json
import os, sys, pathlib #, re, errno
from slugify import slugify
from datetime import datetime
from random import choices as random_choices
from string import ascii_lowercase, digits
from mljob import results_storage
from mljob.run_geneplexus import run_and_save

from mljob.results_storage import ResultsFileStore

job_status_codes = {200:"Completed", 201:"Created", 202:"Accepted", 404:"Not Found", 500:"Internal Server Error", 504:"Timeout"}

    
class LocalLauncher():
    def __init__(self, data_path, results_store):
        self.data_path = data_path
        self.results_store = results_store

    def launch(self,job_name):
        """ launch job.  Inputs = job_config dictionary with parameters.   """
        job_config = self.results_store.read_config(job_name)
        
        if job_config:
            logging.info(f"launching {job_name}")
        
            try:
                gp_ran = run_and_save(job_name, self.results_store, self.data_path, logging = logging, 
                    net_type=job_config.get('net_type'), features=job_config.get('features'), GSC=job_config.get('GSC') )
            except Exception as e:
                return('500')
            
            if gp_ran:
                return('200')
            else:
                return('500')
        else:
            return('404')



class UrlLauncher():
    """ simple class for starting jobs using api (e.g. azure function, container instance, etc). 
    Usage:  
        job_api_url = 'https://some.cloud.account/api/whatever' , or localhost!
        launcher = UrlLauncher(job_api_url)
        job_manager =  JobManager(storage, launcher)
        job_manager.launch(job_config, data)
    """
    def __init__(self,launch_url):
        self.launch_url = launch_url

    def launch(self,jobname):
        """ send the jobname to the URL and return the response.  The queueing functions expect
        and array of jobnames, but just send one"""

        jobname_array_of_one = json.dumps({"jobnames" : [jobname]})
        try:
            logging.info(f"launching {jobname}")
            response = requests.post(url = self.launch_url, data = jobname_array_of_one)
        except Exception as e:
            logging.error("error contacting {self.launch_url} : {e}")
            response = '500'
        
        return(response)    

def generate_job_id():
    """ID generator, 8 alpha numeric characters"""
    eight_char_rand_id = ''.join(random_choices(population = ascii_lowercase + digits, k=8))
    return(eight_char_rand_id)


class JobManager():
    """creates jobs, runs them and checks status"""

    def __init__(self,results_store, launcher):
        self.results_store = results_store
        self.launcher = launcher
        self.required_job_config_keys = ['net_type', 'features', 'GSC','jobname', 'job_url']
        # TODO rename 'job_url' to 'callback_url' which is what it actually is
        # input file name, if we allow a variation on it, should be in job_config


    def cloud_friendly_job_name(self, job_name):
        """ job name must be useable to create file paths and other cloud resources, so remove unuesable or unicode characters"""
        #rules for conainters: The container name must contain no more than 63 characters and must match the regex '[a-z0-9]([-a-z0-9]*[a-z0-9])?' (e.g. 'my-name')."
        # this needs to be idempotent becuase we may call it on an already modified job_name to be safe

        # azure containers must have names matching regex '[a-z0-9]([-a-z0-9]*[a-z0-9])?' (e.g. 'my-name')."
        # this is  more restrictive that file paths.  
        # For slugify, the regex pattern is what to exclude, so it uses the negation operator ^
        # do two passes - one for slugify's chaacter conversion, and one to make it cloud friendly
        filefriendly_job_name = slugify(job_name.lower(), lowercase=True)
        
        cloud_container_exclude_pattern=r'[^a-z0-9]([^-a-z0-9]*[^a-z0-9])?'
        j = slugify(filefriendly_job_name, separator='-', regex_pattern=cloud_container_exclude_pattern)

        return(j)

    def path_friendly_job_name(self, job_name):
        """ for backwards compatibility with existing code """
        return self.cloud_friendly_job_name(job_name)

    def job_exists(self, job_name):
        """ convenience api to detect if job has been started at any time"""
        # assume that if there is an entry in the store, that a job was created 
        return ( self.results_store.exists(job_name) ) 

    def validate_job_config(self, job_config):
        """ validate that job config has what we need to launch """

        # optional_job_keys = ['notifyaddress']
        for k in  self.required_job_config_keys: 
            if not k in job_config:
                logging.error(f"error: job config missing {k}")
                return False
        
        # TODO validate values, perhaps using geneplexus package
              
        return True


    def launch(self, genes, job_config):
        """ start a job by storing the input data and parameters, and using the launcher
        A job gets the following stored
        input file (txt, geneset)
        config file (json) so queue triggered job can read 

        A job launcher gets called with config
        status is returned 
        """
        
        # never trust any inputprep all the filenames and paths
        job_config['jobname'] = self.cloud_friendly_job_name(job_config['jobname'])
        # save this since we use it frequently
        job_name = job_config['jobname']        

        if self.job_exists(job_name):
            logging.error('error: job already exists {job_name}')
            return False
            # this prevents a failed job from being retried

        if not self.validate_job_config(job_config):
            logging.error('invalid job configuration')
            return False

        # passed validation, create storage 
        j = self.results_store.create(job_name)
        
        if not j:
            raise Exception("couldn't create job storage, did not launch job")

        # put the results file there
        job_config['input_file_name']  = self.results_store.save_input_file(job_name, genes)
        logging.info(f"input file = {job_config['input_file_name']}")

        # TODO verify saving notifier address in job info, and can read it
        # change how we we are recovering notifier address (no longer in individual file but part of job_info)
        # remove notifier_file_name = results_store.s_notifyaddress(job_config, app_config)

        # we are misusibng this "save results" method to save an input config file
        job_config_file = self.results_store.save_json_results(job_name, 'job_config', job_config)
        logging.info(f"job_config_file = {job_config_file}")
        # TODO resolve that the 'local' launcher hsa to be given a results-store but URL launcher must self-configure
        response = self.launcher.launch(job_name)

        # TODO need to handle non-OK responses in the job status. e.g. submission failed, need to save that
        self.results_store.save_status(job_name, 'submitted')

        
        return response









