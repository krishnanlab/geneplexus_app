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



Running the Functions Locally
---

Azure has a method for testing these functions on your local compputer.  

**Install**

to run and test locally you'll need to install yet another virtual environment.  I had issue with conda, and as of 2022 the Azure functions does not work with Macs that have Apple Silicon (M1, M2, etc).   For any of this, run in i386 (e.g. Rosetta2) mode.   

When in intel/i386/rosetta mode, install the azure function core tools per microsoft instructions.  These instructions are for command line use, but most MS documentation pushes you to use VSCode.  You don't need to   

Then install a new virtual env, and the convention is to put it into the same folder as the functions but don't check it into git.  There is a requirements file in the mljob folder just for azure functions

```bash
cd mljob
virtualenv .venv -p 3.8
source .venv/bin/activate
# while still in the mljob folder
pip install -r requirements.txt  
```

This virtual env is just for testing the azure functions. 

**Test Run**

When testing the functions, start a new terminal /workspace and activate this environment `cd mljob; source .venv/bin/activate`
 
There is a function endpoint `testfn` that does not require queue triggers and runs the ML code directly.   This 
is for testing only and not meant for the web application, as it will most likely time out if run int he cloud by the app. 

However to truly test the queue-based functions, you need to use a cloud resource group (unless there is an easy way to run a fake queue locally).  So this will still require creating some  Azure resources first.  The Terraform code creates these resources, and by chaning the `env` suffix you can create 
a set of test resources.   See the Terraform directory for detailed instructions. 

Once resources are created, you need need to put the connection string to the queue storage you just created to put into local.settings.json   


1. Create folders on your computer that have a place for jobs ( `/tmp/geneplexus/jobs` perhaps) to go and a copy of all the backend data needed 
 ( `/tmp/geneplexus/data` maybe)
1. get the backend data.   see the script `download_data_for_geneplexus.py`
1. set configuration in a file `local.settings.json` (see the example file provided for syntax):
   ```
    {
      "IsEncrypted": false,
      "Values": {
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AzureWebJobsStorage": "",
        "DATA_PATH" : "/path/on/your/computer/to/geneplexus_data",
        "JOBS_PATH" : "/path/on/your/computer/to/jobs"
        "QUEUECONNECTIONSTRING": "put queue connection string here"
       }
    }
    ```

1. create resources using Terraform (in `./Terraform` directory)
1. get a connection string and put it into local settings file

```
cd mljob
TFDIR=../Terraform/
AZRG=$(terraform output -state $TFDIR/terraform.tfstate -raw AZRG)
AZSA=$(terraform output -state $TFDIR/terraform.tfstate -raw AZSA)
AZFN=$(terraform output  -state $TFDIR/terraform.tfstate -raw AZFN) 
AZSA_CONNSTR=$(az storage account show-connection-string --name $AZSA -g $AZRG --query 'connectionString')
SAKEY=$(az storage account keys list --resource-group $AZRG --account-name $AZSA --query '[1].value')

echo $AZSA_CONNSTR

```

copy and paste that connection string into the "QUEUECONNECTIONSTRING" of `local.settings.json` in order to use the Azure Queue for the 


To start the functions, in the `mljob` folder, start the function server using 

`func start` 

Note there are many tutorials that say you must use VSCode to test and to push functions but you can dmo everything from the CLI. 


creating a local test job folder
---

You need a folder with a job in it to try these functions.   good instructions TBD , but see the python function `local_launcher` in `job_manager.py` 

Testing with Curl
---

curl command to test local processing, (after running `func start`, do this in a new command line window)



curl command to test queue processing:
```bash

LOCALURL='http://localhost:7071/api'

# local test

curl --request GET --location $LOCALURL/testfn \
 --header 'Content-Type: application/json' \
 --data-raw '{"jobname": "8e3jt5kz"}'

curl -X POST ${LOCALURL}/enqueue -H "Content-Type: application/json"    -d '{"jobname": "8e3jt5kz"}'

```

```bash

LOCALURL='http://localhost:7071/api'
# OR
AZURL="https://$AZFN.azurewebsites.net/api"

as a local test, to enqueue to Azure storage, and have your locally running function pick it up and run it

```
curl -X POST ${LOCALTESTURL}/enqueue -H "Content-Type: application/json"    -d '{"jobnames": ["8e3jt5kz"]}
```

curl --request POST --location $LOCALURL \
 --header 'Content-Type: application/json' \
 --data-raw '{"jobnames": ["8e3jt5kz"]}'

curl -X POST $LOCALURL -H "Content-Type: application/json"    -d '{"jobnames": ["8e3jt5kz"]}'

# need to create a job folder in the Azure storage prior to testing on Azure. 

curl -X POST $AZURL -H "Content-Type: application/json"    -d '{"jobnames": ["8e3jt5kz"]}'

curl -X POST $AZURL -H "Content-Type: application/json" -H "x-functions-key: $AZFNKEY"   -d '{"jobid":"somejobid"}'

```


Publishing the code into the function app
---

func azure functionapp publish $AZFN

input to the queue processor is a list of items (document files in the blog post example, but that can be adapted to be jobs)





Background information: Jobs and Results in GPDefinitions 
——

*NOTE: This section is for devs to communicate the application structure and not currently readable, but saved while the app is in development*

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