import logging
import requests
import json
import os, sys, pathlib #, re, errno
from slugify import slugify
from datetime import datetime
from random import choices as random_choices
from string import ascii_lowercase, digits


job_status_codes = {200:"Completed", 201:"Created", 202:"Accepted", 404:"Not Found", 500:"Failed", 504:"Timeout"}

# class Launcher():
#     """ Base """
#     def __init__(self, **kwargs):
#         for k in kwargs:
#             self.k = kwargs[k]

#     def launch(self,job_name):
#         pass

class LocalLauncher():
    """ Run the geneplexus machine learning model code on the current computer, e.g. as a 'job',  triggered by a web application.  
    This is the partner class to UriLauncher which initiates a job by hitting a URL. 
    This is instantiated at app creation time, and sent to the job_manager as the launcher. 
    :param data_path: posix path leading to the backend data. 
    :type data_path: string
    :param results_store: storage class `ResultsFileStore` for working with job input and output data.  
    :type results_store: :class `ResultsFileStore`
    :param callback_url: optional, URI for posting the job status and telling the app the job is complete.  
                         Optional so that testing can proceed without requiring a URL request
    :type callback_url: string that is a valid http or https URL

    """
    def __init__(self, data_path, results_store, callback_url = None):
        """constructor.  Importing geneplexus in private scope since it's only needed for local dev"""
        from mljob.run_geneplexus import run_and_save

        self.run_and_save = run_and_save      
        self.data_path = data_path
        self.results_store = results_store
        
        self.callback_url = callback_url

    def callback(self,jobname, job_status):
        """hit the app just like a remote job runner would do"""
        
        if not self.callback_url:
            logging.error("no callback url set for launcher cancelling callback")            
            return 0
        
        job_callback_url = os.path.join(self.callback_url,jobname)

        json_data = json.dumps({'status' : job_status })
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        callback_resp = requests.post(job_callback_url, json=json_data, headers = headers )
        logging.info(f"launcher hit callback {job_callback_url} with response {callback_resp}")
        return callback_resp


    def launch(self,jobname):
        """ launch job.  Inputs = job_config dictionary with parameters.   """
        job_config = self.results_store.read_config(jobname)
        
        if job_config:
            logging.info(f"launching {jobname}")
    
            try: 
                gp_ran = self.run_and_save(jobname, self.results_store, self.data_path, logging = logging, 
                        net_type=job_config.get('net_type'), features=job_config.get('features'), GSC=job_config.get('GSC') )
                
                print(f"gp_ran = {gp_ran}")

            except Exception as e:
                logging.error(f"{jobname} run error {e}")
                self.results_store.save_status(jobname, job_status_codes[500]) 
                return(500)
            
            if gp_ran:
                logging.info(f"job completed {jobname}")
                self.results_store.save_status(jobname, job_status_codes[200]) 
                print(f"calling back to {job_config['job_url']}")

                resp = self.callback(jobname, job_status=job_status_codes[200])
                print(resp)
                logging.info(f"callback after job success with resp {resp}")
                return(200)
            else:
                logging.error(f"{jobname} failed to complete")
                self.results_store.save_status(jobname, job_status_codes[500]) 
                return(500)
            
        else:
            self.results_store.save_status(jobname, job_status_codes[404])
            logging.error("local launcher; no job config")
            return('404')



class UrlLauncher():
    """ simple class for starting jobs using api (e.g. azure function, container instance, etc). 
    Usage:  
        job_api_url = 'https://some.cloud.account/api/whatever' , or localhost!
        launcher = UrlLauncher(job_api_url)
        job_manager =  JobManager(storage, launcher)
        job_manager.launch(job_config, data)
    """
    def __init__(self,launch_url, logging = logging):
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
    """A helper class for running machine learning jobs as part of the Geneplexus App. Can launch new jobs by working with the store, and checks status
    
    :param results_store: a storage system for writing/reading job data, for example class:`ResultsFileStore`
    :type results_store: class:`results_storage.ResultsFileStore`
    :param launcher: class that supports a `launch(jobname)` method
    :param type: class:`UriLauncher`
    """


    def __init__(self,results_store, launcher, logging = logging):
        """constructor"""
        self.results_store = results_store
        self.launcher = launcher
        self.required_job_config_keys = ['net_type', 'features', 'GSC','jobname', 'job_url']
        # TODO rename 'job_url' to 'callback_url' which is what it actually is
        # input file name, if we allow a variation on it, should be in job_config


    def cloud_friendly_job_name(self, job_name):
        """a job name must be useable to create file paths and other cloud resources, so this method remove unuesable or unicode characters
        and doubles as a security sanitizer
        :param job_name: name of job to sanitize
        :type job_name: string
        :return: sanitized job name
        :rtype: string
        """
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

    def job_exists(self, job_name):
        """checks if job has been started at any time, using method from `results_store`
        :param job_name: name of job 
        :type job_name: string
        :return: True if job exists
        :rtype: Boolean
        """
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
            return None
            # this prevents a failed job from being retried

        if not self.validate_job_config(job_config):
            logging.error('invalid job configuration')
            return None

        # passed validation, create storage 
        j = self.results_store.create(job_name)
        
        if not j:
            raise Exception("couldn't create job storage, did not launch job")

        # put the results file there
        job_config['input_file_name']  = self.results_store.save_input_file(job_name, genes)
        logging.info(f"input file = {job_config['input_file_name']}")

        job_config_file = self.results_store.save_json_results(job_name, 'job_config', job_config)
        logging.info(f"job_config_file = {job_config_file}")

        self.results_store.save_status(job_name, 'submitted')
        response = self.launcher.launch(job_name)
        
        return response

    def job_completed(self, job_name):
        """ standardized method for determining if a job has completed.   If ther status is completed and if 
        parameters: job_name 
        job_status optional job status.  If not provided will be read from the results store.  
        :return: False 
        """

        if not self.results_store.exists(job_name):
            logging.debug("when testing job {job_name}, it does not exist")
            return False
    
        job_status = self.results_store.read_status(job_name)

        logging.debug("checking job completion, job status = {job_status}")
        
        if job_status == job_status_codes[200] and self.results_store.has_results(job_name):
            return True
        else:
            return False

