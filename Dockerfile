# DockerFile for geneplexus Python/Flask application server
# for running on Azure App Service.  Note that Docker is not required to run the 
# Geneplexus Flask application for testing.  This is for deployment to Azure
FROM python:3.8



### ENVIRONMENT
# match local and lang to what is on the MSU HPC as that's how the Pickle files were created
ENV LC_ALL=en_US.UTF-8 \
LANG=en_US.UTF-8 \
LANGUAGE=en_US.UTF-8
# standard lang, which may have issues with pickle (on local docker), or may be a red-herring!
#ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 

# add /usr/local/bin to path as that's where we will put the startup script
# HOME_SITE is default for what Azure app service defaults to
ENV PATH="/usr/local/bin:${PATH}" \
HOME_SITE="/home/site/wwwroot" \
PORT=8000 \
SSH_PORT=2222

EXPOSE 8000 2222

# install additional linux components for app service and ssh server
# and install the libs that this application needs
# create default upload/download directories
# these may not be used depending on ENV config
# then do what's needed to make azure app service ssh work
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales locales-all openssh-server tcptraceroute libxext6 libsm6 libxrender1 curl libglib2.0-0 \
     gfortran libopenblas-dev liblapack-dev  dialog wget bzip2 ca-certificates git \
    && apt-get clean \
    && locale-gen en_US.UTF-8 \
    && mkdir -p /etc/ssh \ 
    && echo 'root:Docker!' | chpasswd \
    && echo "MSU ADS DataScience Flask Application for Azure App Service" > /etc/motd \
    && echo "cd /home" >> /etc/bash.bashrc 

COPY ./azure/sshd_config /etc/ssh/

# if we copy all the application's python files into the Docker image
# we need the statements below
# however for rapid dev, it's better to mount the code folder
# so the docker image does not have be re-created and re-ployedd
# and the code can be updated locaally, and to Azure via git

COPY requirements.txt /var/local

RUN pip install -r /var/local/requirements.txt \
    && pip install subprocess32 gunicorn

# PROPOSED: copy app data into the container to simplify deployment (but not app code)
# but only for data required for geneset validation

# ARG APP_DATA_FOLDER=/usr/local/share/data_backend
# can override this to match where you have the data on your computer now, typically in the .env file
# $ docker build --build-arg APP_DATA_SOURCE=$DATA_PATH
# ARG APP_DATA_SOURCE=app/backend_data
# RUN mkdir $APP_DATA_FOLDER
# COPY $APP_DATA_SOURCE/Node_Orders $APP_DATA_FOLDER
# COPY $APP_DATA_SOURCE/ID_conversion $APP_DATA_FOLDER
# ENV DATA_PATH=$APP_DATA_FOLDER
# IF DATA_PATH not be set in app  .env  OR set in App Service config, 
# then the app will use THAT setting over this one

# NOTES for the app to run,require the FLASK_APP env var to be set
# eg ENV FLASK_APP=app ; typically with the dot-env package

# optional commands... the entry point below will auto-start the web server in the sh script
# CMD ["flask", "run", "-p", "8000"]
# CMD ["gunicorn",  "app:app"]

# server start up and configuration
# you may override these settings by setting GUNICORN_CMD_ARGS var in App service config
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0  --timeout 36000  --log-file /home/site/err.log --workers=4 --threads=8 --worker-class=gthread"
COPY azure/docker-startup.sh /usr/local/bin/startup.sh
RUN chmod a+x /usr/local/bin/startup.sh
ENTRYPOINT ["/usr/local/bin/startup.sh"]
