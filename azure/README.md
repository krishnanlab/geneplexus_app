## Running the Application with Docker And Azure

This folder holds information and files used to create a Docker container that ultimately can run on Azure App Service and Azure storage.  

### Docker

The Azure web service is based on Docker, and the Dockerfile in the root folder is tailored to that.  The Dockerfile is in the root folder makes it easier to build.    Notes on using Docker:

  * it installs an open ssh server for working with the Azure app service which allows you log-in to the running container.  That requires a particular sshdd config file
  * it assumes the application is in the standard folder for App service (/home/site/wwwroot)
  * it does not copy the application files into the container in that folder.   It requires mounting the actually application directory to see the python files
  * Run the flask app using Gunicorn on port 8000

####  Building

From the root folder of the project:

```bash
docker build -t geneplexus:latest .
```

(The name is arbitrary)


####  Running locally

using bash with an external data folder (set the data folder to whereever you have copies of the 'backend' files)

```bash
# example mounted folder on a Mac laptop
export DATAFOLDER=/Volumes/mountedfolder/data_backend
# location of the .env file to use when deployed to azure, 
# but a testing .env file may also be appropriate. 
export DOCKERENV=azure/.env 
# run the image as a container, which launches gunicorn on port 8000
docker run -d  --env-file $DOCKERENV -p 8000:8000 -v $(pwd):/home/site/wwwroot -v $DATAFOLDER:/home/site/wwwroot/app/data_backend   --name geneplexus_container geneplexus:latest

# Did it work?  there should be at least on line in the command
docker ps

# if so then browse to http://localhost:8000

# if not then you can seee the start-up output using 
docker logs geneplexus_container

```



Note The dockerfile starts the webserver automatically, which may make it difficult to debug.  To start a docker container with a bash shell in which you can manually start the webserver or flask shell for debugging, use this  run command (in the main code directory)

```bash
docker run -it  --env-file azure/.env -p 8000:8000 -v $(pwd):/home/site/wwwroot -v  /Volumes/msuhpcc/tmp/data_backend2:/home/site/wwwroot/app/data_backend  --entrypoint=""  geneplexus:latest bash
```


Browse http://localhost:8000    To log-in to the running container with bash: 

```bash
docker exec -it geneplexus_container /bin/bash
```

Updating the source code does not require restarting or rebuilding the docker container, but you'll have to restart to use a different data backend folder, and rebuild if the container needs adjusting. 

#### Start all over

```bash
docker stop geneplexus_container
docker rm geneplexus_container
# re-build
# re-run
```

# Building the Backend Container

There is a second docker container that is for running just the backend.  This uses the same codebase as the app, even though there 
are files and python packages in the app that are unnecessary - it makes it easier to maintain one codebase.  

The Dockerfile is `Dockerfile-backend`

### Preparing data

To download the data for gp, use the geneplexus package as follows (requires the geneplexus package to be installed with pip install geneplexus )

```
import geneplexus, os
from dotenv import load_dotenv

load_dotenv()
data_dir = os.getenv('DATA_PATH')
geneplexus.download.download_select_data(data_dir=data_dir)
```

This downloads zipped files from the data repository Zenodo, unzips and then deletes the zips in the folder you provide.


### build

`docker build -t geneplexus_backend:latest -f Dockerfile-backend .`

notice the trailing dot

### Run

The docker container requires using volume mounts to connect the host to the container.  The two essential paths are for the backend data (DATA_PATH) and input/output.   The input/output path is a folder for keeping job info: input gene file, and results files.  The container runs the pipeline only once, so only needs access to one job folder.  The calling environment mounts this input/output folder from a job folder (on the host computer or in a file share)

Test run (on Linux/MacOS): 

Requires a file for the environt variables to test with, see azure/dockerenv for example. 

example env file to use in docker run command. Note the input/output folder is not set but embedded in GENE_FILE, OUTPUT_FILE, and the -v option (but perhaps it could be as a future development)

```
FLASK_ENV=development
FLASK_DEBUG=TRUE
DATA_PATH=/home/dockeruser/data_backend
GENE_FILE=/home/dockeruser/job/input_genes_newlines.txt
OUTPUT_FILE=/home/dockeruser/job/results.html
GP_NET_TYPE=BioGRID
GP_FEATURES=Embedding
GP_GSC=GO
JOBNAME=docker_job

``` 

Note 1) these values are relative to the container, not your computer and 2) in this file the values must not be enclosed by parenthesis (unlike for MacOS/Linux where this doesn't matter)

Using that env file in practice: 

```
export JOBFOLDER=$(pwd)/testjob
export LOCAL_DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend 
docker run --env-file azure/dockerenv -v $LOCAL_DATA_PATH:/home/dockeruser/data_backend -v $JOBFOLDER:/home/dockeruser/job   geneplexus_backend:latest
```

And what should happen is that you have an html file with the name docker_job.html in the folder

### testing the image by logging in with bash


```
LOCAL_DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend 
docker run -it --env-file azure/dockerenv -v $LOCAL_DATA_PATH:/home/dockeruser/data_backend -v $(PWD):/home/dockeruser/job  --entrypoint=""  geneplexus_backend:latest bash
```

Using On Azure Container Instance

With container instance it's possible to mount multiple shares (one for backend data, one for results) but here we are just using one for simplicity (otherwise we need to use ARM templates). 


# Azure

The application and job-running system currently runs on Azure cloud.   

## Architecture


## Building the services in Azure

Azure services can be created in many ways ( web 'portal', Python, Templates) but these instructions use the command line utility (CLI) `az` in the terminal.  The script `create_azure_services.sh` is a collection of bash functions for creating the services necessary for the geneplexus application and jobs to run

### Requirements

  * an Azure account and subscription in which you can create objects (e.g. with funding)
  * bash.  This script was tested on MacOS.  If on linux, ignore the 'open' commands.  Not tested but it should work using the Windows Subsystem for Linix (WSL)
  * Azure CLI installed
    - Microsoft instructions for installation : https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
    - Note that it may be possible to use Anaconda for this instead to be able use environments. This worked in 2020
      `conda install -c conda-forge azure-cli-core`
    - after installation, test the install at the terminal with `az login`, and log-in.  If you can't log-in, these scripts won't work
    - may need to add extensions `az extension add --name webapp`
  * It assumes your Azure CLI is configured and logged in 
  * in the home directory of this project's folder (folder with the file `Dockerfile`)
  * a configuration file named .azenv in same format as the usual .env in the azure folder
     - the .env file in your directory is not copied into the docker container
     - the .azenv file is for azure webapp 'appsettings' which translate to env vars in th container
  * basic understanding and previous experience with Azure
  * basic understanding of Docker
  * decide on some names for your azure services  : a resource group name, and a project name.  These are set with env variables

### OPTIONAL
  * Docker installed for your platform 
  * an existing Azure resource group 

### How-To

tldr; 

```bash
source azure/azuredeploy.sh
az login


# if you use multiple subscriptions, there is currently not a great way to select the one you want
# so you have to do it manually 
# list all your subs
az account list
# list the currently select subscription ID

az account show --query id --output tsv

# you may have to change that for this script
az account set --subscription "some long subscription id"
# and/or
export AZSUBID="some long subscription id"

# you can also set that using the function
az_check_account

# next, select an 'environment' for a suffix for all names, dev, test, prod, qa, whatever and set the rest of the variables
export PROJECTENV=test1
az_set_vars $PROJECTENV

# this simple function doesn't have a good way to set the TAG used for all the docker containers. 
# set the tag now for docker to current date, or whatever you want (v3, latest, etc)
export TAG=`date +"%Y.%m.%d"`    

# note what the az_set_vars used for the resource group
echo $RG

```
Start in the root dir of the project.  Open a bash terminal, open the environment or how you use the az command line,  and log-in to azure with   `az login`

Review the functions in the script `azure/azuredeploy.sh` 

In that script, the first function `az_set_vars()` is used to set environment variables.  check and adjust the values
in the script for your needs.  Note you can override those. 
 
source the file to load the functions into your process :  `source azure/create_azure_services.sh`

set the base env variables used throughout the functions : `az_set_vars`


