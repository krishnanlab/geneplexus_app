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

using bash with an external data folder: 

```bash
export DATAFOLDER=/Volumes/hpchome/data_backend

docker run -d  --env-file azure/.azenv -p 8000:8000 -v $(pwd):/home/site/wwwroot -v /Volumes/hpchome/data_backend:/home/site/wwwroot/app/data_backend   --name geneplexus_container geneplexus:latest
```

Did it work?  `docker ps`

Note The dockerfile starts the webserver automatically, which may make it difficult to debug.  To start a docker container with a bash shell in which you can manually start the webserver or flask shell for debugging, use this  run command (in the main code directory)

```bash
docker run -it  --env-file azure/.azenv -p 8000:8000 -v $(pwd):/home/site/wwwroot -v /Volumes/hpchome/data_backend:/home/site/wwwroot/app/data_backend  --entrypoint=""  geneplexus:latest bash
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
source azure/create_azure_services.sh
az_set_vars
echo $RG

```
Start in the root dir of the project.  Open a bash terminal, open the environment or how you use the az command line,  and log-in to azure with   `az login`

Review the functions in the script `azure/create_azure_services.sh` 

In that script, the first function `az_set_vars()` is used to set environment variables.  check and adjust the values
in the script for your needs.  Note you can override those. 
 
source the file to load the functions into your process :  `source azure/create_azure_services.sh`

set the base env variables used throughout the functions : `az_set_vars`


