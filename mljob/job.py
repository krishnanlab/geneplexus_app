# jobs.py  Class to work with submitted LogicApp jobs

import os,json, sys, requests
from datetime import datetime
from slugify import slugify

class Jobs():
    """ system for managing running jobs  Usage: 
    from mljob.job import Jobs

    # in app init, put the class inside the app
    app.jobs = Jobs
    # set the configuration
    app.jobs.job_config = app.config  # don't need all of the config, but this is easy

    # in views

    from app import app
    def retrieve_job(jobname):
        if (app.jobs.job_exists(jobname)):
            job = app.jobs(jobname)

    """
    # this is  set once for all jobs and used during app life cycle
    config  = {'JOB_PATH' : 'jobs', 
                'JOB_CONTAINER_FILE_MOUNT': 'jobs', 
                'JOB_URL': "http://localhost:5000/localjob"}


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

    @classmethod
    def path_friendly_jobname(cls,jobname):
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


    # TODO rename standard job folder
    @classmethod
    def retrieve_job_folder(cls,jobname):
        """ return the job folder based on current config, or empty string if no job folder exists"""

        jobname = Jobs.path_friendly_jobname(jobname)
        job_folder = os.path.join(cls.config.get("JOB_PATH"), jobname)
        if os.path.isdir(job_folder):
            return(job_folder)
        else:
            return('')


    @classmethod
    def job_exists(cls,jobname):
        """look up job based on job config"""
        jobname = cls.path_friendly_jobname(jobname)
        jf = cls.retrieve_job_folder(jobname)
        if jf:
            return(True)
        else:
            return(False) 

    @classmethod
    def list_all_jobs(cls): 
        """ given the path where jobs live, pull the list of all jobs """
        job_path = cls.config['JOB_PATH']

        with os.scandir(job_path) as jobdir:
            joblist = [d.name for d in jobdir if d.is_dir() and not d.name.startswith('.')]
        return(joblist)  

    @classmethod
    def valid_results_filename(possible_file_name):
        """convert user input into value OS filename, strip out most punctuation and spacing, preserve case. 
        The goal is to reduce risk of security problems from user input but allow what should be a valid
        results file name.  This does not limit to what we may know as valid file names"""

        file_regex_pattern = r'[^-A-Za-z0-9_\.]+'
        slugified_file_name = slugify(possible_file_name, lowercase=False,regex_pattern=file_regex_pattern)
        return(slugified_file_name)



#==============
    def __init__(self, job_config):
        self.config = job_config
        self.jobname =  Jobs.path_friendly_jobname(job_config.get('job_name'))


    def job_status(self):
        """ use methods above to construct and return the state of the job"""
        jf = self.retrieve_job_folder()
        if not jf:
            return('4o4')

    def input_file_name(self):
        return('input_genes.txt')
        # jn = path_friendly_jobname(jobname)
        # return (f"{jn}_input.txt")

    def results_file_name(self):
        return("results.html")
        # jn = path_friendly_jobname(jobname)
        # return (f"{jn}_results.html")

    def json_file_name(self):
        jn = Jobs.path_friendly_jobname(self.jobname)
        return(f"{jn}.json")

    def job_json(self):
        """build the data payload for the http trigger """ 
        # TODO remove the hard-coded "jobs" folder here and set as config value
        # the job folder ('jobs') must be in sync in the app and the job-runner container setting
        # TODO remove all of this cloud config from this app! 
        # most does not change from job-to-job, so set it when creating the logic app
        # these values are set or can be discovered using commands in the CLI script. so perhaps they need to go 
        # direct into the ARM template  (as params to the template), since they don't affect the app. 

        job_path=f"{Jobs.config.get('JOB_CONTAINER_FILE_MOUNT')}/jobs/"
        
        input_file_name = self.input_file_name()
        results_file_name = self.results_file_name()

        #  "imageName": f"{acrname}.azurecr.io/{Jobs.config.get('JOB_IMAGE_NAME']}:{app_config['JOB_IMAGE_TAG')}",
        docker_image_config = {
            "imageName": f"{Jobs.config.get('CONTAINER_REGISTRY_URL')}/{Jobs.config.get('JOB_IMAGE_NAME')}:{Jobs.config.get('JOB_IMAGE_TAG')}",
            "registry": {
                "server": Jobs.config.get('CONTAINER_REGISTRY_URL'),
                "username": Jobs.config.get('CONTAINER_REGISTRY_USER'),
                "password": Jobs.config.get("CONTAINER_REGISTRY_PW")
            }
        }

        volume_config = {
            "name": "geneplexusfiles",
                    "mountPath": Jobs.config.get('JOB_CONTAINER_FILE_MOUNT'),
                    "readOnly": False,
                    "shareName": Jobs.config.get("STORAGE_SHARE_NAME"),
                    "shareReadOnly": False,
                    "storageAccountName": Jobs.config.get("STORAGE_ACCOUNT_NAME"),
                    "storageAccountKey": Jobs.config.get("STORAGE_ACCOUNT_KEY")
        }

        # TODO see above, set most of this when creating the logic app
        # TODO remove the hard-coded data folder, and set this as an env var
        envvars = {
            "FLASK_ENV": "development",
            "FLASK_DEBUG": True,
            "GP_NET_TYPE": self.config.get('net_type'),
            "GP_FEATURES": self.config.get('features'),
            "GP_GSC": self.config.get('GSC'),
            "JOBNAME": self.config.get('jobname'),
            "JOBID": self.config.get('jobid'),
            "DATA_PATH": f"{Jobs.config.get('JOB_CONTAINER_FILE_MOUNT')}/data_backend2/",
            "GENE_FILE": f"{job_path}/{self.config.get('jobname')}/{input_file_name}",
            "OUTPUT_FILE": f"{job_path}/{self.config.get('jobname')}/{results_file_name}",
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


    def launch_job(self,genes):
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
        jobname = Jobs.path_friendly_jobname(self.config.get('jobname'))
        # jobid = self.config.get('jobid')
        input_file_name = Jobs.create_input_file_name(jobname)
        json_file_name = Jobs.create_json_file_name(jobname)
        local_job_folder = f"{Jobs.config['JOB_PATH']}/{jobname}"


        input_file_path = f"{local_job_folder}/{input_file_name}"
        json_file_path = f"{local_job_folder}/{json_file_name}"

        #TODO use these tidied-up file names in the job_config
        job_data = self.job_json()
        
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
        response = requests.post(Jobs.config['JOB_URL'],
                            data=job_data,
                            headers=jsonHeaders)

        print(f"Job data sent for {jobname}.  Status code: {response.status_code}", file=sys.stderr)

        return response

    def results_file_dir(self,data_file_name = None):
        """return to flask the absolute path to a data file to be returned for download, 
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
            data_file_name = Jobs.create_results_file_name(self.jobname)
        else:
            data_file_name = Jobs.valid_results_filename(data_file_name)

        # get the path this job
        jf = Jobs.retrieve_job_folder(self.jobname) # get path if job exists, or return ''
        if jf:
            data_file_path = os.path.join(jf, data_file_name)
            if os.path.exists(data_file_path):
                return(jf)
            
        return(None)

    
    def results_file_path(self,results_file = None):
        """construct the path to the job (for local/mounted file storage)"""
        # use the default name if none given 
        if not ( results_file) :
            results_file = self.results_file_name()

        jf = self.retrieve_job_folder()
        if jf:
            return(os.path.join(jf, results_file))
        else:
            return(None)

    def check_results(self, jobname):
        """"  return T/F if there is a results file """
        fp = Jobs.results_file_path(jobname)
        #  if results file exists and it's non-zero size, then true
        return( os.path.exists(fp) and os.path.getsize(fp) > 0) 

    def retrieve_job_params(self):
        """construct the path to the job (for local/mounted file storage)"""    
        job_folder = self.retrieve_job_folder()
        if job_folder:
            params_file_path = os.path.join(job_folder, self.json_file_name())
        else:
            return('')

        if os.path.exists(params_file_path):
            with open(params_file_path) as f:
                content = f.read()

            params_vars = json.loads(content)

            return(params_vars['envvars'])
        else:
            return('')


    def retrieve_results_data(self,data_file_name):
        """get any one of several of the results data files (TSV, JSON, etc)
        This does not check if the file name is one of the 'approved' file names to give 
        flexibility to the job runner during development"""

        data_file_name = Jobs.valid_results_filename(data_file_name)

        # TODO define standard filenames for various results types and vet data file name as security precaution
        jf = self.retrieve_job_folder() # get path if job exists, or return ''

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



    def job_info(self):
        """ return a dict of job info for jobs table (no results) """

        # create default empty dict for consistent rows
        job_info = { 
            'jobname': self.jobname,
            'is_job' : False,
            'submit_time' : None,
            'has_results' : '',
            'params' : {},
            'status' : 'NOT FOUND'
        }

        jf = self.retrieve_job_folder()
        if jf:
            job_info['is_job'] = True
            job_info['submit_time'] = datetime.fromtimestamp(os.path.getmtime(jf)).strftime("%Y-%m-%d %H:%M:%S")
            job_info['has_results'] = self.check_results()
            job_info['params']= self.retrieve_job_params()
            job_info['status']= self.retrieve_job_status()
        else:
            job_info['is_job'] = False
            job_info['status'] = 'NOT FOUND'

        return(job_info)


# RUNNING LOCALLY: shoud still use a shell script, just like a remote job
# And return control to the app rather than make it wait. 
# if Jobs.config['RUN_LOCAL']:
#             print("running job locally (may take a while")
#             html_output = run_and_render(genes, net_type=self.config.get('net_type'], features=self.config.get('features'), GSC=job_config['GSC'), jobname=jobname, output_path=local_job_folder)

#             # TODO find the method here that constructs a results file! 
#             results_file = os.path.join(local_job_folder, 'results.html')
#             with open(results_file, 'w') as f:
#                 f.write(html_output)
#             response = "200"