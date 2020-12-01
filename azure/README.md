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