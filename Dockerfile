# DockerFile for geneplexus application
#
FROM python:3.9

### ENVIRONMENT
# match local and lang to what is on the MSU HPC as that's how the Pickle files were created
ENV LC_ALL=en_US.UTF-8 \
LANG=en_US.UTF-8 \
LANGUAGE=en_US.UTF-8
# standard lang, which may have issues wiht pickle (on local docker), or may be a red-herring!
#ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 

# add /usr/local/bin to path as that's where we will put the startup script
# HOME_SITE is default for what Azure app service defaults to
ENV PATH="/usr/local/bin:${PATH}" \
HOME_SITE="/home/site/wwwroot" \
PORT=8000 \
SSH_PORT=2222

ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0  --timeout 36000  --log-file /home/site/err.log --workers=4 --threads=8 --worker-class=gthread"

EXPOSE 8000 2222

# install additional linux components for app service and ssh server
# and install the libs and pandoc stuff that this application needs
# create default upload/download directories
# these may not be used depending on ENV config
# then do what's needed to make azure app service ssh work
RUN apt-get update \
    && apt-get install -y  locales locales-all openssh-server tcptraceroute libxext6 libsm6 libxrender1 curl libglib2.0-0 \
       dialog wget bzip2 ca-certificates git \
    && apt-get clean \
    && locale-gen en_US.UTF-8 \
    && mkdir -p /etc/ssh \ 
    && echo 'root:Docker!' | chpasswd \
    && echo "MSU ADS DataScience Flask Application for Azure App Service" > /etc/motd \
    && echo "cd /home" >> /etc/bash.bashrc 


    # && mkdir -p $HOME_SITE \
    # && mkdir -p $HOME_SITE/instance && mkdir -p $HOME_SITE/instance/uploads && mkdir -p $HOME_SITE/instance/downloads



COPY ./azure/sshd_config /etc/ssh/

# if we copy all the application's python files into the Docker image
# we need the statements below
# however for rapid dev, it's better to mount the code folder
# so the docker image does not have be re-created and re-ployedd
# and the code can be updated locaally, and to Azure via git

COPY requirements.txt /var/local

RUN pip install -r /var/local/requirements.txt \
    && pip install subprocess32 gunicorn


# WORKDIR $HOME_SITE
# temporary copy the web application files into the container
# for production app, comment these out and use git deployment
# COPY app app
# COPY azure/.azenv .env
# COPY config.py .

# TODO test if we need this set here, or can set as web app config
# ENV FLASK_APP=app
# settings required by azure
# and recommended on https://pythonspeed.com/articles/gunicorn-in-docker/
# --worker-tmp-dir /dev/shm (add this is running Linux)


# CMD ["flask", "run", "-p", "8000"]
# CMD ["gunicorn",  "app:app"]

COPY azure/docker-startup.sh /usr/local/bin/startup.sh


RUN chmod a+x /usr/local/bin/startup.sh
ENTRYPOINT ["/usr/local/bin/startup.sh"]
