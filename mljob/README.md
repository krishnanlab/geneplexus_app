Managing Jobs with modules and classes in mljob package

Organization
---

 - geneplexus = imported from PyGeneplexus, not managed here
 
 - results_store = ResultsFileStore : class to read/write inputs and outputs to a 'store' by providing many convenience wrapper methods.   
   The only methods working now is a file store, requiring data on the computer or mounted e.g. for Azure Files.   


 - run_geneplexus.py  = generic wrapper around geneplexus and the resultstore.  Uses results store to get inputs (geneset) from a dataStore,
   reads a job config for params, invokes geneplexus and save data in the dataStore.  Logs to dataStore
   Designed to be called fromr a cloud function, your laptop, or from the app directly on computer/laptop (e.g. during dev)

 - launcher: class with one method : launch.  gathers, checks input params, creates the job store, calls run_geneplexus, sends status back
    - web azure launcher
    - local launcher 
 
 - job_manager = links the application with the launcher, puts the inputs gathers by the app into the dataStore so the launcher can find it. 
    designed to call either web launcher or cloud via an API (e.g. URL)

 - results = TBD


Jobs and Results in GPDefinitions 
——

job = common api for starting ML processes and check status of those process
sending parameters to the machine to create results.   
output of a job is the status of that job, and messages about how it's doing (run time, memory, cost?)

Once a job is done, status = completed and we need nothing more from it. 
if job is completed, it doesn’t have a purpose.    
the output of a job is status and link to results

if a job is complete, can  it be used to create results object? 

class properties
    status_codes
    update_url
    job_path
    notifier
    notify_address

state
    exists (t/f) (class method)
    status 
    status_code
    completed (t/f)  (state == COMPLETED)
    job_config == params, inputfile

verbs
    set_config(app_config)
	start : (id, job_config, app_config)  JOB MANAGER begin running, or submit it to the runner  (Not ‘submit’ as a job does _not_ necessarily require a queue). 
        save params to job_info file
        save input data to JobManager.job_path
        start process (URL)


	get_status : checking a job).  JOB MANAGER See what the process is doing. 
    update : send an update from  JOB MANAGER
    get_results : return(Results.get(self.id)  results factory to create a results ojbect from this job

	should a job when checking return a ‘results’ object?

    cleanup : remove resources if necessary once completed (e.g. delete container)
        
    we want to be able to run a job locally and on a queue (and maybe some other way)
    results = storage of output from d


JobRunner
    imports JobManager
    reads config from disk

    


Results = 
    the output fro the machine learning code
    inputs (params + user data + system data) 
	# code. = ML functions 
	
	infrastructure to read save output

	

process
 app init:  
    app.results_store = ResultsFileStore(app.config['JOB_PATH'])
    job_manager = JobManager(launcher, app.results_store)
    
    

new job = to submit and run the job

```
job = JobManager(job_name, job_config, app_config )  #  job_config ==> params etc
if job_name doesn't already exist => self.results_store.exists()
    response_code = job.submit()  # put response and other info into job class, 
        # create folder, and/or database entry
        # hit job runner URL and get response
    # if there is problem submitting job :
    #   # reset? delete all entries in database?
    #   # simply set that there was an error submitting with details and leave job in DB?
    # else no problem
    #   flash 'all good'
else: # job exists already!!! 
    # the users _may_ not know there is already a job and may not want to load it
    # especially if the job is not owned by the user, or is meant ot be private
    # but could instead just load what      
```


"""

generic geneplexus runner : run_geneplexus.py
---

this is a function to be called by any sub process or app itself.  it has three main parts 
1) the launcher that preps storage and kicks it off from the web or other process
2) the controller that gathers configuration and parameter, and imports the relevant libs, sets up storage class
3) a call to the function that will run the ML code that sends params, config and objects needed. 
   this function run_gp() should be useable for any runner

Note: could be possible to create generic runml() class and associated resultsStore class (since results are specific to )

### runner requirements:
- job_name set , geneset and info is saved and prepped in store keyed on job_name
- data is available to runner
- job info is available to runner

### inputs: 

- params: 
    - job_name
    - callback_url
    - other ML params,e.g. max_num_genes
- config: job path (and in future even access keys) for results store, data path for gp

### imports:
- ResultsStore, JobManager, Runner, Geneplexus

### types of launchers: 
- URL-type: send job params to URL, call_back address for status
- local-type: sends params and config values for function -> send resultStore???

cloudrunner using FileStore 
- job & data folders mounted
- config: set when app is deployed
- param: job_name in request
- imports: ResultsFileStore, JobManager, Runner, Geneplexus
- sets up results_store
- sets up logger (to file in results_store? or some other cloud-based log)
- updates status using results_store
- calls runml
- hits callback_url with status

local runner
- job & data folders must be reachable
- config data_path sent as param
- config job_path OR send the resultsStore object that's already  configed
- param: job_name in cli or call
- imports: ResultsFileStore, JobManager, Runner
- sets up results_store
- sets up logger (to file in results_store?)
- updates status using results_store
- calls runml
- hits callback_url with status if provided, else prints status on command line



def runml(job_name, resultsp, data_path, logger):

if name is main: 
    set up results store,  file-based (by default), could send the name of the class to instantiate?
    job_path
    data path is CLI param
    job id is CLI param
    
# cli usage ==> runner.py job_name, job_path, data_path
    

called by azure fn : 

get config from OS  (job_pat, data_path)
get params from request
setup results store
"""