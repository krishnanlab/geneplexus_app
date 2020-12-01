#!/bin/sh
set -e

# custom startup script the Dockerfile entrypoint
# currently not used. Azure Dockerfiles have over-complete startup scripts to 
# accommodate many different types of applications

# put versions in the logs
python --version
pip --version

# ensure ssh service is going using systemd 
echo "Starting SSH ..."
service ssh start

# Get environment variables to show up in SSH session
eval $(printenv | sed -n "s/^\([^=]\+\)=\(.*\)$/export \1=\2/p" | sed 's/"/\\\"/g' | sed '/=/s//="/' | sed 's/$/"/' >> /etc/profile)

cd $HOME_SITE
# flask run -p 8000
export GUNICORN_CMD_ARGS="--bind=0.0.0.0  --timeout 36000  --log-file /home/site/err.log --workers=2 --threads=4 --worker-class=gthread"
gunicorn  --timeout 36000 --bind=0.0.0.0:8000 app:app