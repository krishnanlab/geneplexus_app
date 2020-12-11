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

The Dockerfile is `Dockerfile_backend`


### build

`docker build -t geneplexus_backend:latest -f Dockerfile_backend .`

notice the trailing dot

### Run

Test run (on Linux/MacOS): 

```
LOCAL_DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend 
docker run --env-file azure/dockerenv -v $LOCAL_DATA_PATH:/home/dockeruser/data_backend -v $(PWD):/home/dockeruser/job   geneplexus_backend:latest
```

And what should happen is that you have an html file with the name docker_job.html in the folder

### testing the image by logging in with bash


```
LOCAL_DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend 
docker run -it --env-file azure/dockerenv -v $LOCAL_DATA_PATH:/home/dockeruser/data_backend -v $(PWD):/home/dockeruser/job  --entrypoint=""  geneplexus_backend:latest bash
```