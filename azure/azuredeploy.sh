# GenePlexus App Azure Deployment
# ===
# bash script using Azure CLI code to create
# Azure Container Registry (AZCR)  and Docker containers
# App Service  ( & Plan ) , File Storage
# and creates a script to run on HPC to azcopy data to File Storage
# Logic App that creates the 'aci' Container Instances, connector API to 
# 

# REQUIREMENTS
# ---
#   * an Azure account in which you can create objects
#   * bash.  This script was tested on MacOS.  If on linux, ignore the 'open' commands
#   * Azure CLI installed (I installed via Miniconda into a conda environment) (see below)
#   * It assumes your Azure CLI is configured and logged in 
#   * an existing Azure resource group
#   * set the default Azure location (could to the group to, but I didn't)
#       az configure --defaults location=westus2 group=MyResourceGroup
#   * a project with a Dockerfile and a web app  
#   * a configuration file for azure  in same format as the usual .env
#      - the .env file in your root directory is not copied into the docker container by default
#      - the default filename azure/.env file is for azure webapp 'appsettings' which translate to env vars in th container
#      - the exact file is set in the variable $ENVFILE
#
# OPTIONAL
#   * Docker installed for local testing.  the commands here use the Azure Container Registry tasks for docker

# GET STARTED 
# ---
# three methods : on Mac use HomeBrew, Use Anaconda, or use the azure Cloudshell
# install python  
#   on Mac Microsoft recommends homebrew but that will install a _ton_ of packages
#   including a new python install.   Even if you do az upgrade, this invokes homebrew
#   Anaconda might work. I've gone back and forth.  Currently using homebrew because had an issue with ua  
# using Anaconda:  create an environment and install the az cli python library
#   strongly suggest create a different environment from your application environment
#   Azure is not in the requirements.txt because the app does not require it to run (only deploy)
#   conda create --name azure pip
#   conda activate azure
#   pip install azure
#   az login 

# using Azure cloudshell
# ---
# the Azure portal has a bash shell that has the az CLI pre-installed
# see the Azure documentation on cloud shell for detailed
# to use it with this script.
# start the cloud shell
# git clone <repo url> 
# cd <repo folder>
# create/edit the file azure/.env 
# note since you aren't running the flask app itself here, can use 
# use the instructions as you would if it were on your computer 


##### USAGE
# 1. IMPORTANT you must review the values in the az_set_vars() function below FIRST
#    things to check:
#    TAG = the docker container TAG 
#    PROJECT : name of the project (used for all resources with env
#    CLIENT : name of the lab/person this is for 
#    PROJECTENV (default is dev) which you set with param value to when calling az_set_vars


##
# 2. source this file
# source azure/azuredeploy.sh

##
# 4. log-in to azure (requires azure cli to be available)
# az login
#   note if you have access to multiple azure subscriptions, you may have to set it manually 
#    list all subs:        az account list --output table
#    set the sub to use:   az account set --subscription <subid>

##
# 4. determine the name of the 'environment' you want to build for : dev, test, prod or other, 

## 
# 4. run the build_all function with that environment, eg. for dev
# build_all dev
#
# note this will not re-create an existing resource group or resources
# you may have to manually delete them in Azure portal first
# some commands must be run manually - for one the command to copy files from the HPC to Azure

##
# 5. perform additional manual steps (see comments in the build_all() function)
#

##
# 6. git push flask app to app service
# the build should print your new git remote and give commands to push the app pyhon code to the 
# new app service which does not contain code

# 7. test
# manually run a sample job 

echo "Azure Deployment Bash Functions.  To use thi script you must have th az command line instlled, and be "
echo "Logged in with az login ; set the variable AZSUBID ; run the bash function az_set_vars, and check value of \$TAG "
az_build_all ()
{
  # build all the resources needed to run the gene plexus application
  # to run these manually stepy by step (e.g. copy/paste to terminaal), you must manually run the command
  #  export PROJECTENV=test 
  # first
    az_check_account
    if [ -z "$AZSUBID" ]; then 
        echo "No Azure Subscription Found - perhaps you need to use az login first?" >&2 
        return 1
    fi

    if [ -n "$1" ]; then
        export PROJECTENV=$1
    else
        echo "project environment name required (dev, test, prod for production, etc, eg"
        echo 'e.g., $ build_all test'
        return 1
    fi
    
    az_set_vars $PROJECTENV   # or other environment name
    # add variable overrides here! e.g use 
    
    echo "creating resources for app $AZAPPNAME in $AZRG..."
    az_create_group

    # STORAGE
    az_create_file_storage
    # copy files from HPCC to this new storage created
    HPCC_FOLDER=/mnt/ufs18/rs-027/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend2
    az_copy_hpcc_to_files $HPCC_FOLDER
    #read -n 1 -p "Confirm the azcopy command worked (y) to continue  or any key to stop script (y/)" CMDCONFIRM
    #if [[ "$CMDCONFIRM" == "y" || "$CMDCONFIRM" == "Y" ]]
    #then
    #    echo "continuing app deployment"
    #else 
    #    "command completion not confirmed, exiting..."
    #    exit 1
    #fi


    # Containerized web application Service
    # create container registry and build container
    az_create_app_registry  
    # create app service plan, service, and set config
    az_create_webapp 
    az_app_set_container
    az_app_mount_file_storage

    # build container for model runner, and set app config for jobs
    az_build_docker_backend

    # create API connection to Container instance for a controlling account
    # create logic_app that allows the app to create container instances
    # set the app config to the HPCC endpoint for this new logic app
    az_logic_app_create


}

az_set_vars ()
{
    # set global vars used by other functions below
    # this function must be run first.  

    # first set the azure subscription
    az_check_account  # side-effects: sets AZSUBID, exits if not logged in
    
    # set user id to use for subsequent commnds. 

    
    export AZFULLUSER=$(az account show --query="user.name")  # this include @msu.edu
    export AZUSER=`echo $AZFULLUSER | cut -d "@" -f1 | tr -d '"'`  # strip off the @msu.edu , which leaves leading quote that needs to be deleted too
    
    # if there is none (AZSUBID var is empty), then we exit with an error message 
    if [ -z "$AZSUBID" ]; then 
        echo "No Azure Subscription Found - perhaps you need to use az login first?" >&2 
        exit 1
    fi


    # PROJECTENV should be one of dev, test, prod per IT Services standard practice
    # but this only requires it's set; if not default to 'dev'
    if [ -n "$1" ]; then
        export PROJECTENV=$1
    else
        export PROJECTENV=dev
    fi

    # this is required and set per projects
    export PROJECT=geneplexus
    export CLIENT=krishnanlab
    
    # set the resource group name based on project name and environment (dev, qa, prod)
    export AZRG=$CLIENT-$PROJECT-$PROJECTENV 

    echo "Using project suffix '$PROJECTENV' and resource group '$AZRG'" >&2  

    # run the function below to see if the group exists, and if not, recommend creating it
    if ! check_az_group_exists; then
        echo "Resource group $AZRG doesn't exist, use the az_group_create function or CLI command"
    fi

    # note from microsoft about A container registry names: 
    # Uppercase characters are detected in the registry name. When using its server url in docker commands, to avoid authentication errors, use all lowercase.    
    # NOTE from Azure: 'registry_name' must conform to the following pattern: '^[a-zA-Z0-9]*$'  eg no hypens etc
    export AZCR=${CLIENT}${PROJECTENV}cr  #  in future use a department-wide container registry for all projects

     export AZAPPNAME=${PROJECT}${PROJECTENV}   # modify this if there are multiple/different apps per project
   

    # docker container names and tags
    export AZDOCKERIMAGE=$PROJECT
    export BACKEND_IMAGE=${AZDOCKERIMAGE}-backend
    # if the tag is already set, it will use that.  
    DEFAULT_TAG=latest
    export TAG="${TAG:-$DEFAULT_TAG}"
    echo "using docker container name and tag ${AZDOCKERIMAGE}:${TAG}"
    export AZPLAN=${PROJECT}-plan
    export AZLOCATION=centralus # centralus may not have Container Instances needed 
    export ENVFILE=.env-azure
    export AZTAGS="createdby=$AZUSER project=$PROJECT environment=$PROJECTENV" 
    export AZ_SERVICE_PLAN_SKU="B2"  # "S1"  # see https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
    # apps like gunicorn or DJango run on port 8000
    # if you are testing a flask app dev server, change this to 5000
    # but don't use flask app dev server for production!
    export PORT=8000
    # DOCKER

    export AZSTORAGENAME="${PROJECT}${PROJECTENV}"
    export AZCONTAINERNAME="${PROJECT}-container"
    export AZSHARENAME="${PROJECT}-files-$PROJECTENV"

    export AZGITUSERNAME=$AZUSER

}

# confirm that there is an az account (and user is logged in) 
az_check_account () 
{
    # check that there is an azure subscription for you
    export AZSUBID=$(az account show --query id --output tsv)

    # if there is none (AZSUBID var is empty), then we exit with an error message 
    if [ -z "$AZSUBID" ]; then 
        echo "No Azure Subscription Found - perhaps you need to use az login first?" >&2 
        exit 1
    fi

}

# confirm that resource group exists
# if the resource group doesn't exists, most functions below won't run
check_az_group_exists ()
{    
    if [[ "`az group exists --name $AZRG`" == "false" ]]
    then
        # echo "Resource group $AZRG doesn't exist, use the az_group_create function or CLI command"
        # echo "az group create --location $AZLOCATION --name $AZRG --tags $AZTAGS"
        return 1
    else
        return 0
    fi
}

### should check if $AZRG is a group and if not create it
# example group create
az_create_group () 
{
    if check_az_group_exists
    then
        echo "resource group $AZRG already exists"
    else
        echo "creating resource group $AZRG"
        az group  create --location $AZLOCATION --name $AZRG --tags $AZTAGS
    fi
}

#########
## build)   
## TODO check if a registry exists and if not build it
az_create_app_registry()
{
    echo "MAKE A REGISTRY $AZCR in group $AZRG"
    az acr create --name $AZCR --resource-group $AZRG --sku Basic --admin-enabled true
    # we need a password from the AZCR for other steps
    # this uses the Azure CLI JMSEpath and TSV ouutput to extract the first of two passwords
    # note this has been replaced by used of stdin password below
    # acrpw=`az acr credential show --name $AZCR -g $AZRG  --output tsv  --query="passwords[0]|value"`

    # always build, assume running to rebuild
    echo "using azure acr to build the files in this repository"
    az_build_container
    # az acr build -g $AZRG -t $AZDOCKERIMAGE:$TAG -r $AZCR .

    # alternative - AZCR task queue
    # echo "queue azue acr task that builds from a github repository."
    # echo "unless you have CI/CD/Git hooks configured, push to github first"
    # az acr task run -n build_$AZDOCKERIMAGE -r $AZCR -c <github url> -f Dockerfile

    az acr repository list -n $AZCR
    #read -n1 -r -p "is the image $AZDOCKERIMAGE on this list? Press n to exit script" key
    #if [ "$key" = 'n' ]; then
    #    echo "repository error, exiting"
    #    return 1
    #fi
}


az_create_webapp ()
{
    echo "Make a web app  $AZAPPNAME  in group $AZRG using custom dockerfile $AZDOCKERIMAGE:$TAG"
    # requirements: working Dockerfile, created resource group and AZCR in that group
    # also reads a local .env file
    # make an app,  and tell it about the registry
    az appservice plan create --name $AZPLAN --resource-group $AZRG --location $AZLOCATION --number-of-workers 2 --sku $AZ_SERVICE_PLAN_SKU --is-linux --tags $AZTAGS

    # commands to use a container registry that requires credentrials - not neeed for an AZCR in the same subscription
    # export AZ_ACR_PW=$(az acr credential show --name $AZCR -g $AZRG  --output tsv  --query="passwords[0]|value")
    # az webapp create -g $AZRG -p $AZPLAN -n $AZAPPNAME --tags $AZTAGS \
            # --deployment-container-image-name $AZCR.azurecr.io/$AZDOCKERIMAGE:$TAG  \
            # --docker-registry-server-user $AZCR  \
            # --docker-registry-server-password $AZ_ACR_PW


    # CLI to create web app using custom container from 'local' Azure container repository (AZCR)
    # deployment local git from https://docs.microsoft.com/en-us/azure/app-service/deploy-local-git?tabs=cli
    # https://docs.microsoft.com/en-us/azure/app-service/scripts/cli-deploy-local-git?toc=/cli/azure/toc.
    az webapp create -g $AZRG -p $AZPLAN -n $AZAPPNAME \
            --deployment-local-git \
            --deployment-container-image-name $AZCR.azurecr.io/$AZDOCKERIMAGE:$TAG  \
            --tags $AZTAGS 

    # TODO: see how to use these for for CI/CD from gitlab
                #  [--deployment-local-git]
                #  [--deployment-source-branch]
                #  [--deployment-source-url]

    # Azure documentation say this is on by default, but it doesn't seem to be.  You must turn it on manually like this
    # this allows the /home/site/wwwroot folder to be mounted into the custom container 
    # which allows us to "deploy from local git" or `git push` our app scripts to update the app, 
    # rather than 
    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true

    # note - setting the docker image from AZCR in this way fails the log-in
    # use the method below to send a password 
    
    #  -i $AZCR.azurecr.io/$AZDOCKERIMAGE:$TAG 
    # this assumes there is a file with the name you set the variable $ENVFILE above 
    # that contains config values for flask to run in Azure
    # and this command translates a .env file with a space-seperated list for az cli

    # use a function below to set the app  ENV setting (azure calls these env vars configuration)
    az_webapp_setconfig
    
    az webapp log config --name $AZAPPNAME \
            --resource-group $AZRG \
            --application-logging  filesystem \
            --docker-container-logging filesystem \
            --level information


    # app "identity" allows this app to access things like storage accounts without your user ID (e.g. app-level IAM)
    # TODO : is this necessary? 
    # this doesn't seem to create a new identity if one exists, just returns existing identity UUID
    export AZAPPIDENTITY=$(az webapp identity assign --resource-group $AZRG --name $AZAPPNAME --query principalId --output tsv)
    

    # git deployment of code (not container)
    # the container does not contain the python code, that gets deployed to standard folder on the app service "machine"
    az webapp deployment source config-local-git \
        -g $AZRG -n $AZAPPNAME


}

# return an apps "identity" code
# this is used to grant the application access to the az storage container
# so that the azure files storage can be mounted on the app
az_get_app_identity () 
{
    az webapp identity show --resource-group $AZRG --name $AZAPPNAME --query principalId --output tsv

}

# this sets up your LOCAL git repository to be able to push to this
# azure app service created above
az_git_setup ()
{
echo "your azure deployment user is: $AZGITUSERNAME" 
    
    AZREMOTENAME=azure
    AZGITREMOTE=https://$AZGITUSERNAME@$AZAPPNAME.scm.azurewebsites.net/$AZAPPNAME.git
    # TODO test if the current azure remote is the same, then no need to delete and re-add

    # in this folders git comit, 
    echo "updating yuor git remotes for azure deploy "
    echo "removing existing remote $AZREMOTENAME"
    git remote remove $AZREMOTENAME
    echo "adding azure git remote $AZREMOTENAME as $AZGITREMOTE"
    git remote add $AZREMOTENAME $AZGITREMOTE
    CURRENTBRANCH=`git branch --show-current`
    echo "your next step is to run command:"
    echo "git push $AZREMOTENAME $CURRENTBRANCH:master"
    echo "to deploy the website, using the deployment password you've set. "

    ## NEXT 
    # the dockerfile does not contain the app scripts, only software to run it
    # use the portal to set your userid and password for "local git deploy",
    # and portal to copy/paste the deployment git URL, 
    # add that remote to your app repository and push
}

## set application-level configuration using a env file from this repository
# The app will use these settings (in app service configuration) over any .env file 
# settings, because these settings are OS Env vars set when the container starts up
az_webapp_setconfig ()
{
    # read the file $ENVFILE, and convert to space delimited set of values
    AZ_ENV_VARS=`paste -sd " " $ENVFILE`
    # set the values from the ENVFILE in the webapp
    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings WEBSITES_PORT=$PORT $AZ_ENV_VARS

}

az_browse_webapp () 
{
    # does it work?  
    # It takes a good 5 minutes to copy the container from AZCR to app service
    # you could also check on  the Azure portal for your resoruce group, 
    # there is is a button for container logs
    open http://$AZAPPNAME.azurewebsites.net

    # also try to access the control panel for this 
    open http://$AZAPPNAME.scm.azurewebsites.net
}


az_build_container ()
{
    # use Azure Container registry task to build the docker container in Dockerfile
    # requires the presence of a working Dockerfile, which may require many other things
    echo "building image $AZDOCKERIMAGE:$TAG in azure cr $AZCR using Dockerfile"
    az acr build -t $AZDOCKERIMAGE:$TAG -r $AZCR .
}


# this will set/reset the image to be used for the container for the web app
# the container is initially set above when the web app is created
# run this if you update the container , or need to use a different image:tag name
az_app_set_container ()
{
   az webapp config container set --name $AZAPPNAME --resource-group $AZRG --docker-custom-image-name ${AZCR}.azurecr.io/$AZDOCKERIMAGE:$TAG --docker-registry-server-url https://${AZCR}.azurecr.io

   # this setting gets set to false sometimes (but not always).  so set to true AGAIN here
   az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
   # is manual restart needed, or is it auto-restarted when config is changed?
   az_app_restart

}



# builds the "backend" container, or the one that just runs the ML code in model.py on a container instance
function az_build_docker_backend () {
    #THIS HAS TO BE RUN _after_ THE WEB APP IS CREATED
    # TAG is set in azure_set_vars
    # check if this var is set, and if not, set to a default name
    if [[ -z "$BACKEND_IMAGE" || -z "$TAG" ]]; then
        echo "image name vars not set - Please run az_set_vars function first "
        exit 1
    fi

    export AZBACKENDIMAGE_URL=$ACR.azurecr.io/$BACKEND_IMAGE:$TAG  
    # needed for the logic app! 

    # TODO set this in az_set_vars, not here, and confirm file exists
    export JOB_DOCKERFILE="Dockerfile-backend"  
    # the name of the file in this project
    # echo "using Azure ACR to build docker image $BACKEND_IMAGE:$TAG from $JOB_DOCKERFILE with callback to https://{$AZAPPNAME}.azurewebsites.net/jobs"
    az acr build --build-arg APP_POST_URL_ARG=https://$AZAPPNAME.azurewebsites.net/jobs  -t $BACKEND_IMAGE:$TAG -r $AZCR --file $JOB_DOCKERFILE .

    # then should update the application settings - requires the web app to exist first, 
    # but the webapp can't run jobs without the backend container
    # this is where the job container volumn mount point is truly defined for the first time
    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME \
    --settings JOB_IMAGE_NAME=$BACKEND_IMAGE JOB_IMAGE_TAG=$TAG \
     JOB_CONTAINER_FILE_MOUNT=/home/dockeruser/$AZSHARENAME \
     CONTAINER_REGISTRY_URL=$AZCR.azurecr.io CONTAINER_REGISTRY_USER=$AZCR \
     CONTAINER_REGISTRY_PW=$(az acr credential show --name $AZCR -g $AZRG  --output tsv  --query="passwords[0]|value")
}


az_local_docker_build_backend ()

{
    # this is a function to use local docker to build local image for testing
    # this isn't needed for Azure deploy other than for testing
    # the name of the file in this project
    export JOB_DOCKERFILE="Dockerfile-backend"  
    echo "Building docker $BACKEND_IMAGE:$TAG  from $JOB_DOCKERFILE with callback to https://{$AZAPPNAME}.azurewebsites.net/jobs"
    docker build --build-arg APP_POST_URL_ARG="https://{$AZAPPNAME}.azurewebsites.net/jobs"  -t $BACKEND_IMAGE:$TAG --file $JOB_DOCKERFILE .
    docker images 
    echo "Did the docker image $BACKEND_IMAGE:$TAG build? "
    echo "to run, copy and past this... "
    "docker run -d -v $DATA_PATH:$OUTPUT_PATH -e DATA_PATH=$DATA_PATH --name ${AZDOCKERIMAGE}_container $BACKEND_IMAGE:$TAG"    
}

# this is a work in progress and not used, saved here for experiments =
# Azure App Service has a concept of "slots" so you can deploy updates
# without disturbing your existing application
# this is only necessary if you update the Dockerfile for the main app 
# and is not needed to simply update the code - use Git deploy for that.  
# not that Staging could be used for git deployment to test a codebase without stopping
# the running production application (on the same App Service Plan)
az_app_stage ()
{
    az_build_container

    SLOTNAME=staging

    az webapp deployment slot delete  --name $AZAPPNAME  \
            --resource-group $AZRG  \
            --slot $SLOTNAME \

   # create "slot for staging and copy from the 
    az webapp deployment slot create --name $AZAPPNAME  \
            --resource-group $AZRG  \
            --slot $SLOTNAME \
            --configuration-source $AZAPPNAME

    az_app_set_container

    # preview (works on mac)
    open http://${AZAPPNAME}.azurewebsites.net/?x-ms-routing-name=${SLOTNAME}

}

# WIP
# this is used along with staging an app on app service
# after staging in a slot and then testing that the code/container for that slot is working
# 
az_app_set_production_container () 
{
        az webapp config container set --name $AZAPPNAME  \
            --resource-group $AZRG  \
            --docker-custom-image-name $AZCR.azurecr.io/$AZDOCKERIMAGE:$TAG  \
            --docker-registry-server-url https://$AZCR.azurecr.io  \
            --docker-registry-server-user $AZCR  \
            --docker-registry-server-password $(az acr credential show --name $AZCR -g $AZRG  --output tsv  --query="passwords[0]|value")
}

az_app_update_container () 
{
    # rebuild from the docker file on the Azue AZCR
    # and then update the app to use this new container
    ### NOTE this doesn't update the c
    az_build_container
    az_app_set_container
}

az_app_restart () 
{
    az webapp restart --name $AZAPPNAME -g $AZRG
}


az_app_update ()
{
    # function to only update the application when the vars have been set
    # if the AZRG, registry, app service plan, and app service have all been created, 
    # then all that needs doing is to rebuild the container (assumes the Dockerfile is good
    # for a valid build) and update the container config for the web app
    # and restart the web application

    az_build_container

    az webapp config container set --name $AZAPPNAME  \
            --slot $
            --resource-group $AZRG  \
            --docker-custom-image-name $AZCR.azurecr.io/$AZDOCKERIMAGE:$TAG  \
            --docker-registry-server-url https://$AZCR.azurecr.io  \
            --docker-registry-server-user $AZCR  \
            --docker-registry-server-password $(az acr credential show --name $AZCR -g $AZRG  --output tsv  --query="passwords[0]|value")

    # not sure if this is necessary, or if config above will trigger a restart
    az webapp restart

}

# local Docker test
# does the docker file and app even work? if you have docker you caould build it and run it
# make sure you dont' have any other containers/apps running on localhost:8000
# if you've tried this before you may have to stop the container and rmi the image

az_local_docker_build ()
{
    # this is a function to use local docker to build local image for testing
    # this isn't needed for Azure deploy other than for testing
    docker build --tag $AZDOCKERIMAGE:$TAG .

    docker images 
    read -n1 -r -p "Did the docker image build? Pres 'n' to exit script" key

    if [ "$key" = 'n' ]; then
        echo "docker couldnt' build app, exiting"
        return 1
    fi


    ### TEST that the dockerfile can run and works locally (optional)
    echo "running application and opening browser..."
    # this requires a file to hold the environment variables for running locally
    docker run -d -p ${PORT}:${PORT} --env-file .dockerenv --name ${AZDOCKERIMAGE}_container $AZDOCKERIMAGE:$TAG
    open http://localhost:$PORT  # check it

    #    read -n1 -r -p "Did the website open? Pres 'n' to exit script" key
    # if [ "$key" = 'n' ]; then
    #     echo "docker couldnt' run app, exiting"
    #     return 1
    # fi
}





az_app_delete ()
{
# Once you are done, tear it all down by running this function in the same terminal

    echo "this deletes ALL the things related to app $AZAPPNAME app, plan, repo"
    echo "this doesn't delete the database, but does delete all files,logs etc from app VM"
    echo "deleting app $AZAPPNAME"
    az webapp delete --resource-group $AZRG --name $AZAPPNAME
    echo deleting appservice $AZPLAN
    az appservice plan delete --resource-group $AZRG --name $AZPLAN

}

az_acr_image_delete ()
{
    echo deleting docker image $AZDOCKERIMAGE:$TAG from $AZCR

    # note if you just want to replace the latest image, 
    #you can delete just one tagged image of the repository
    az acr repository delete --name $AZCR --repository  $AZDOCKERIMAGE

}

az_acr_delete ()
{
    echo deleting repository $AZCR
    az acr delete --resource-group $AZRG --name $AZCR 

}

az_local_docker_teardown ()
{
    echo deleting docker image $AZDOCKERIMAGE:$TAG
    docker rmi $AZDOCKERIMAGE
    docker rmi $AZDOCKERIMAGE:$TAG
}


#################
# storage account 
# this is used for mounting files to the web application to access large files
# so that they do not go into the container itself or sit on the web app

az_create_blob_storage ()
{
export AZSTORAGESKU="Premium_LRS"
export AZBLOBSTORAGENAME="${AZAPPNAME}blobstorage"
export AZCONTAINERNAME="${AZAPPNAME}backend"

az storage account create -g $AZRG --name $AZSTORAGENAME -l $AZLOCATION \
    --sku $AZSTORAGESKU --kind BlobStorage \
    --tags $AZTAGS
}

##############################
##### CREATE FILE STORAGE


# get a storage account key for given storage name - 
get_storage_key()
{
  THIS_STORAGE_ACCOUNT=${1:-$AZSTORAGENAME}
  STORAGE_KEY=$(az storage account keys list --resource-group $AZRG --account-name $THIS_STORAGE_ACCOUNT --query "[0].value" --output tsv)
  echo $STORAGE_KEY
}

az_create_file_storage ()
{

export AZSTORAGESKU="Premium_LRS"

# cheaper options 
# SKU=Standard_LRS
az storage account create -g $AZRG --name $AZSTORAGENAME -l $AZLOCATION \
    --sku $AZSTORAGESKU --kind FileStorage \
    --tags $AZTAGS

export AZSTORAGEKEY=$(az storage account keys list -g $AZRG -n $AZSTORAGENAME --query '[0].value' -o tsv)

az storage share create --account-name  $AZSTORAGENAME \
    --name $AZSHARENAME --account-key $AZSTORAGEKEY
# 7/2021: The documentation says to use the option  '--enabled-protocols SMB' but then there is this unrecognized arguments error
# per MSFT ticket, this option is no longer supported (or necessary apparently)

}

az_app_mount_file_storage ()
{
    # mounts the file storage onto the app as a network drive (SMB by default)
    # the Flask app itself ONLY uses this for the gene validation step
    # then set the webapp config for the data path so the Flask app knows where to look

    # NOTE there is a different ENV variable for where to look for jobs, but this is the same storage account (but in the /jobs folder)

    MOUNTPATH=/home/site/$AZSHARENAME/
    # HARDCODED sub-folder in this deploy script.  This is where the flask app will look, 
    # and depends on how the data is copied into storage from HPCC
    APP_DATA_FOLDER=$MOUNTPATH/data_backend2 
    APP_JOB_FOLDER=$MOUNTPATH/jobs  #/home/site/data

    
    # this is the name of the env variable the flask app is looking for 
    # hard coded in the flask app, use variable here to make it explicit
    APP_VARIABLE_FOR_MOUNTPATH="DATA_PATH"
    APP_VARIABLE_FOR_JOBPATH="JOB_PATH"

    ## to access the storage, the app needs an "identity"  
    # see function az_get_app_identity() and this is run when the app is created above

    # requires storage account has been created
    AZSTORAGEKEY=$(az storage account keys list -g $AZRG -n $AZSTORAGENAME --query '[0].value' -o tsv)

    # NOTE to simply make a change to the path that is mounted, use 
    # az webapp config storage-account update -g $AZRG -n $AZAPPNAME \
    #   --custom-id $AZAPPIDENTITY \
    #   --mount-path $MOUNTPATH


    # add a new mount, will error if storage key is blank
    az webapp config storage-account add --resource-group $AZRG \
        --name $AZAPPNAME \
        --custom-id $(az_get_app_identity) \
        --storage-type AzureFiles \
        --share-name $AZSHARENAME \
        --account-name $AZSTORAGENAME --access-key $AZSTORAGEKEY \
        --mount-path $MOUNTPATH

    
    # NOW set config for the app, so it can send via a logic app to the backend job (see jobs.py)
    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME \
    --settings ${APP_VARIABLE_FOR_MOUNTPATH}=$APP_DATA_FOLDER ${APP_VARIABLE_FOR_JOBPATH}=$APP_JOB_FOLDER \
    STORAGE_ACCOUNT_KEY=$AZSTORAGEKEY STORAGE_ACCOUNT_NAME=$AZSTORAGENAME STORAGE_SHARE_NAME=$AZSHARENAME 

}



# use the function above to mount storage;
# use this only to updaate the mount point (or refresh?)
# normally this function is not necessary
az_update_file_storage ()
{
    az webapp config storage-account update -g $AZRG -n $AZAPPNAME \
    --custom-id $AZAPPIDENTITY \
    --mount-path $MOUNTPATH
}


#############
#  LOGIC APP 
# integration between web app and backend container
# THIS DOES NOT WORK using the envsubst method
az_logic_app_create ()
{
    # assumes we are running in the project root dir
    # and that the definition file is in the azure/ subdir
    # this function is specific to this application and the file name embedded here
    # and assumes there is this logic app definition file, that contains the env variables in it 
    # with the extension ".bash"  (not sure why I picked that! it's a template template)
    # that are defined above $AZRG etc.  
    # a better solution is to use ARM template and a parameter file for all of these params (sub id, res group, etc)    
    # reference: https://docs.microsoft.com/en-us/azure/connectors/apis-list

    echo "Creating ACI API connection for logic app to use  "
    arm_template_file='azure/aci_api_connection_template.json'
    ACI_CONNECTION_NAME=${PROJECT}acirunner 
    
    # JOB_URL='https://prod-02.northcentralus.logic.azure.com:443/workflows/d7b7c90d031547fd989687f5b7e66287/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ZO2XtJ8cFUwUmr_rxHU-YbWG8YEDO22M3EtqekhHPHU'

    if [[ -f "$arm_template_file" ]]; then
        az deployment group create \
        --name  ${PROJECT}${PROJECTENV}aciapi  \
        --resource-group $AZRG \
        --template-file $arm_template_file \
        --parameters connection_name=$ACI_CONNECTION_NAME environment=$PROJECTENV azlocation=$AZLOCATION projectname=$PROJECT azuser=$AZUSER

    else
        echo "error, the arm template file for api connection not found : $arm_template_file"
    fi

    # these are hard-coded values that are also in the json template
    # and must sync with that 

    LOGICAPP_ARM_TEMPLATE_FILE='azure/aci_logicapp_template.json'
    ARM_PARAMETERS_FILE='azure/aci_logicapp_template_parameters.json'
    WORKFLOW_NAME="geneplexus-runmodel"
    TRIGGER_NAME="manual"


    echo "running ARM template $LOGICAPP_ARM_TEMPLATE_FILE "
    az deployment group create \
    --resource-group $AZRG \
    --template-file  $LOGICAPP_ARM_TEMPLATE_FILE \
    --parameters @${ARM_PARAMETERS_FILE} \
    --parameters connection_name=$ACI_CONNECTION_NAME workflow_name=$WORKFLOW_NAME trigger_name=$TRIGGER_NAME \
    --name $PROJECT_logicapp_deployment_$PROJECTENV 
    
    echo "add tags to the logic app $WORKFLOW_NAME"
    LOGICAPPID=`az logic workflow show -g $AZRG --name "$WORKFLOW_NAME" --query id`
    echo Due to azure bug, the following can\'t be run from this script, but will run if you copy/paste, to set tags on logic app

    settagscmd="az tag create --resource-id $LOGICAPPID --tags created_by=$AZUSER project=$PROJECT environment=$PROJECTENV"
    echo $settagscmd
    
    echo "setting app config to use the HTTP URL for this logic app trigger URL..."
    # we need to get the Logic app trigger URL to set the config for the flask application.  Only Powershell and REST API are supported (no )
    # REF https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-actions-triggers
    LOGICAPP_APIVERSION="2016-06-01"  
    # template says 2017-07-01 but this is the only one that seems to work 

    # reference https://docs.microsoft.com/en-us/rest/api/logic/workflow-triggers/list-callback-url
    # to get the list of "names" of triggers, use az rest --url "https://management.azure.com/subscriptions/$AZSUBID/resourceGroups/$AZRG/providers/Microsoft.Logic/workflows/$WORKFLOW_NAME/triggers?api-version=$LOGICAPP_APIVERSION"

    # construct the API URL to get our Logic APP URL
    API_URL_TO_GET_LOGICAPP_URL="https://management.azure.com/subscriptions/$AZSUBID/resourceGroups/$AZRG/providers/Microsoft.Logic/workflows/$WORKFLOW_NAME/triggers/$TRIGGER_NAME/listCallbackUrl?api-version=$LOGICAPP_APIVERSION"
    # call the rest API with the URL above to get our Logic APP URL
    LOGICAPP_TRIGGER_URL=$(az rest --method post --url $API_URL_TO_GET_LOGICAPP_URL --output tsv --query "value")  
      # output tsv required to avoid quoted value
    # set config so the flask app can use this URL when submitting jobs
    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings JOB_URL=$LOGICAPP_TRIGGER_URL

    # THIS URL IS NOT TIME SENSITIVE AND WILL WORK FOR ANY IP ADDRESS 
    # example JOB URL
    # JOB_URL='https://prod-02.northcentralus.logic.azure.com:443/workflows/d7b7c90d03blahblahblah/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ZO2XtJ8cFUwUmr_rxHblahblahblah'

    # authorizing logic app API connectors musdt be done manually, or with a service principal (which we would need to request)
    # REFERENCE https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-deploy-azure-resource-manager-templates#authorize-oauth-connections
    echo "MANUAL CONFIGURATION REQUIRED: open this URL to authorize the API connection:"

    export AZDIRECTORY=olucdenver  # switch back to msu.edu if necessary
    echo "https://portal.azure.com/#@$AZDIRECTORY/resource/subscriptions/$AZSUBID/resourceGroups/$AZRG/providers/Microsoft.Web/connections/$ACI_CONNECTION_NAME/edit"

https://portal.azure.com/#@olucdenver.onmicrosoft.com/resource/subscriptions/d67ad5df-1a15-47ba-897c-fa549b7b9a1d/resourceGroups

}

# set the hostname for the app service to use
az_set_app_hostname ()
{
# this command may not be enough to confirm this hostname may be used 
# (may require confirmation with the hostname registrar and DNS settings)
if [[ -z "$1" ]]; then
    echo "Usage: az_set_app_hostname <fulll hostname.com>"
else  
    echo "configuring app to use hostname $1..."
    az webapp config hostname add \
    --webapp-name $APPNAME --resource-group $RG \
    --hostname $1
     
    echo "try browsing http://$1 to see $APPNAME"
fi
}


# BACK END DATA COPY HPCC TO CLOUD
# create the params needed for azcopy to work from HPCC
# note you need generate a token with Azure, which requires you to know the IP address
# of the HPCC system we are copying from, and getting that requires using SSH, which needs your NETID. 
# in this draft, using $AZUSER as proxy for netid but for everyone but me, that's probably not going to work
# this also use ssh to log-in and run the command on hpcc but
# this simply echos the command to run to copy and paste  
# see https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-files
# example successful az copy command: 
#  azcopy copy /mnt/ufs18/rs-027/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend2 https://geneplexusdev.file.core.windows.net/geneplexus-files-dev/$AZSASTOKEN --recursive
# requirements: HPCC account set HPCC_FOLDER to current location of backend files, and you have access to that
# tested on MacOS but should work on Linux or anything with `ssh` command
az_copy_hpcc_to_files ()
{

    # check for required params and env vars

    if [[ -z "$1" ]]; then 
        echo "source file folder path argument is required.  Usage: "
        echo "$ az_copy_hpcc_to_files /mnt/ufs18/rs-027/etc/etc/etc"
        return 1
    else
        if [[ -z "$AZSTORAGENAME" || -z "$AZSHARENAME" ]]; then
            # values $AZSTORAGENAME $AZSHARENAME required
            echo "please run az_set_vars first to set storage names (and also run az_create_storage)"
            return 1
        fi
    fi

    SOURCEFOLDER=$1  # TODDO validate that this folder exists/is accessible from here     
    # this option needed to get a SAS token is for blob storage, doesn't work for Azure files
    AZSTORAGEKEY=$(az storage account keys list -g $AZRG -n $AZSTORAGENAME --query '[0].value' -o tsv)

    # this option is for azure files NOTE the identity is not used for azcopy
    # the identity is used to grant access FROM the appservice TO the storage for when the storage is mounted
    # I'm leaving this here for now but it's not relevant
    # this assumes the identity was set
    # TODO check if an identity is actually set, and if not, set one
    # AZAPPIDENTITY=$(az webapp identity show --resource-group $AZRG --name $AZAPPNAME --query principalId --output tsv)
    
    # MacOS only.  zNrrf yo 

    TOMORROW=$(date -v+1d  +%Y-%m-%dT%H:%MZ)
    # this is a wider range than needed but right now includes their 4  ssh gateways and 
    # maybe he GUI gateways like on-demand
    HPCC_IP_RANGE="35.9.12.1-35.9.12.255"
    
    
    # BLOB STORAGE 
    # az storage container generate-sas \
    # --auth-mode key
    # --ip $HPCC_IP
    # --account-name $AZSTORAGENAME \
    # --name $AZCONTAINERNAME \
    # --permissions acdlrw \
    # --expiry $TOMORROW \
    # --auth-mode login \
    # --as-user)


    # FILE STORAGE SAS token
    # to use 
    # https://docs.microsoft.com/en-us/cli/azure/storage/share?view=azure-cli-latest#az_storage_share_generate_sas
    AZSASTOKEN=$(az storage share generate-sas \
        --name $AZSHARENAME \
        --account-name $AZSTORAGENAME \
        --account-key $AZSTORAGEKEY \
        --ip $HPCC_IP_RANGE\
        --https-only --permissions dlrw --expiry $TOMORROW -o tsv)

    # az copy command how-to : https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-files
    # URL template 'https://<storage-account-name>.file.core.windows.net/<file-share-name><SAS-token>' 
    # example 'https://mystorageaccount.file.core.windows.net/myfileshare?sv=2018-03-28&ss=bjqt&srs=sco&sp=rjklhjup&se=2019-05-10T04:37:48Z&st=2019-05-09T20:37:48Z&spr=https&sig=%2FSOVEFfsKDqRry4bk3qz1vAQFwY5DDzp2%2B%2F3Eykf%2FJLs%3D'
    AZSTORAGEURL=https://${AZSTORAGENAME}.file.core.windows.net/${AZSHARENAME}\?${AZSASTOKEN}


    export AZCOPY_CMD="azcopy copy $SOURCEFOLDER '$AZSTORAGEURL' --recursive"
    echo "the azcopy command for this app is :"
    echo ""
    echo $AZCOPY_CMD
    echo ""
    echo "you may have to copy/paste this into an HPCC session, and you must have the azcopy utility installed"
    echo "note the single quotes around the azure storage URL are required"
    if [[ -z "`which ssh`" ]]; then 
        echo "no ssh command found (maybe you are on Windows?) then manually log-in and run the above"
    else
        # assume that the Azure user id is the same as your hpcc user id
        # this is true for all MSU accounts (uses NetID by default) 
        ssh ${AZUSER}@hpcc.msu.edu $AZCOPY_CMD
    fi
}

# pull the info from az storage for use with 
# the az copy command
az_storage_endpoint_info ()
{
    httpEndpoint=$(az storage account show \
    --resource-group $AZRG \
    --name $AZSTORAGENAME \
    --query "primaryEndpoints.file" | tr -d '"')

    smbPath=$(echo $httpEndpoint | cut -c7-$(expr length $httpEndpoint))
    echo "$AZSTORAGENAME samba path = $smbPath"

    fileHost=$(echo $smbPath | tr -d "/")
    echo "$AZSTORAGENAME  filehost = $fileHost"


}


## storage stuff
## example of the kind of command that is generated 
# the command can only execute of you have access to the folder you are copying from
# NOTE the destination MUST be single-quoted as there are special chars in the SAS URL 'sig' parameter
# azcopy copy /mnt/ufs18/rs-027/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend2 'https://geneplexusdev.file.core.windows.net/geneplexus-files-dev?Z4FS10CC9zGyudRa8wdbfuS4CW%2BhdGeu6I5iu9edy8o'
# AZSASTOKEN='?sv=2020-02-10&ss=f&srt=sco&sp=rwdlc&se=2021-03-27T00:54:34Z&st=2021-03-25T16:54:34Z&sip=172.16.93.1-172.16.93.255&spr=https,http&sig=SOMELONGSTRINGWITH%ANDOTHERCHARS'


### container group management

# at one point the container groups were not auto deleted post-job and must be manually managed
# the following functions will count group in the resource group for the env set above, and delete them

az_count_acis ()
{
    echo "number container groups in resource group $AZRG:"
    az container list -g $AZRG --query "[].name" -o tsv | wc -l
}

az_delete_completed_acis ()
{
    # this deletes all container groups in the current resource group that have completed
    
    for n in `az container list -g $AZRG  --query "[].name" -o tsv`; do
        # get status of first container (only one container for these ACI groups)
        ACISTATE=`az container show -g $AZRG --name $n --query "containers[0].instanceView.currentState.detailStatus"`
        if [[ "$ACISTATE" == "\"Completed\"" ]]; then
            echo "deleting ACI $n"
            az container delete -g $AZRG --name $n -y
        fi
    done
}