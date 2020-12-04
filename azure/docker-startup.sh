#!/usr/bin/env bash
set -e

# custom startup script the Dockerfile entrypoint
# currently not used. Azure Dockerfiles have over-complete startup scripts to 
# accommodate many different types of applications



cat >/etc/motd <<asciiart 
     MSU Analytics and Data Services
     /\__\         /\  \         /\__\    
    /::|  |       /::\  \       /:/  /    
   /:|:|  |      /:/\ \  \     /:/  /     
  /:/|:|__|__   _\:\~\ \  \   /:/  /  ___ 
 /:/ |::::\__\ /\ \:\ \ \__\ /:/__/  /\__\
 \/__/~~/:/  / \:\ \:\ \/__/ \:\  \ /:/  /
       /:/  /   \:\ \:\__\    \:\  /:/  / 
      /:/  /     \:\/:/  /     \:\/:/  /  
     /:/  /       \::/  /       \::/  /   
     \/__/         \/__/         \/__/    
      ___           ___           ___     
     /\  \         /\  \         /\  \    
    /::\  \       /::\  \       /::\  \   
   /:/\:\  \     /:/\:\  \     /:/\ \  \  
  /::\~\:\  \   /:/  \:\__\   _\:\~\ \  \ 
 /:/\:\ \:\__\ /:/__/ \:|__| /\ \:\ \ \__\
 \/__\:\/:/  / \:\  \ /:/  / \:\ \:\ \/__/
      \::/  /   \:\  /:/  /   \:\ \:\__\  
      /:/  /     \:\/:/  /     \:\/:/  /  
     /:/  /       \::/__/       \::/  /   
     \/__/         ~~            \/__/    
      Data Science Development Docker
  
asciiart
cat /etc/motd

# put versions in the logs
python --version
pip --version

# ensure ssh service is going using systemd 
echo "Starting SSH ..."
service ssh start

# Get environment variables to show up in SSH session
eval $(printenv | sed -n "s/^\([^=]\+\)=\(.*\)$/export \1=\2/p" | sed 's/"/\\\"/g' | sed '/=/s//="/' | sed 's/$/"/' >> /etc/profile)

# note: this env variable moved to Dockerfile, so that it may be overriddend with -e param during docker run
# export GUNICORN_CMD_ARGS="--bind=0.0.0.0  --timeout 36000  --log-file /home/site/err.log --workers=2 --threads=4 --worker-class=gthread"
if [ -d "$HOME_SITE" ] 
then
    echo "Starting gunicorn, serving from HOME_SITE=$HOME_SITE"
    echo "using GUNICORN_CMD_ARGS=$GUNICORN_CMD_ARGS"
    gunicorn  --chdir $HOME_SITE --bind=0.0.0.0:8000 app:app
    
else
    echo "Error: HOME_SITE=$HOME_SITE not found, webserver not started"
fi

