# Syllabuster App Azure Depoloyment
# ===
# bash script using Azure CLI code to create
# Azure Container Registry (AZCR) 
# App Service
# App Service Plan
# Postgresql database
# based on  https://docs.microsoft.com/en-us/azure/app-service/containers/tutorial-custom-docker-image

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
#   * Docker installed for local testing

# GET STARTED 
# ---
# install python  
#   on Mac Microsoft recommends homebrew
#   Anaconda also works 
# create an environment and install the az cli python library
#   I suggest create a different environment from your application environment
#   Azure is not in the requirements.txt because the app does not require it to run (only deploy)
#   conda create --name azure pip
#   conda activate azure
#   pip install azure
#   az login 


az_set_vars ()
{
    # ==========
    # variables
    
    export PROJECT=geneplexus
    export CLIENT=krishnanlab
    export PROJECTENV=dev  # one of dev, qa, prod per IT Services standard practice 
    export AZRG=$CLIENT-$PROJECT-$PROJECTENV 


    

    # note from microsoft about A container registry names: 
    # Uppercase characters are detected in the registry name. When using its server url in docker commands, to avoid authentication errors, use all lowercase.    
    # NOTE from Azure: 'registry_name' must conform to the following pattern: '^[a-zA-Z0-9]*$'
    export AZCR=${CLIENT}cr  #  in future use a department-wide container registry for all projects


    # if this is the production version, do no 
    if [ "$PROJECTENV" == "prod" ]
    then
        export AZAPPNAME=${PROJECT}
    else
        export AZAPPNAME=${PROJECT}${PROJECTENV}   # modify this if there are multiple/different apps per project
    fi

    export AZDOCKERIMAGE=$AZAPPNAME
    export TAG=2021.03  # TODO => rename to AZDOCKERTAG
    
    
    export AZPLAN=${PROJECT}-plan
    export AZAPPNAME=$PROJECT

    export AZLOCATION=east # centralus may not have Container Instances needed 
    export ENVFILE=azure/.env
    export AZTAGS="createdby=$USER project=$PROJECT" # to do t
    export AZ_SERVICE_PLAN_SKU="B2"  # "S1"  # see https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
    # apps like gunicorn or DJango run on port 8000
    # if you are testing a flask app dev server, change this to 5000
    # but don't use flask app dev server for production!
    export PORT=8000
    # DOCKER

    export AZSTORAGENAME="$PROJECT-st-$PROJECTENV"
    export AZCONTAINERNAME="${PROJECT}-stcontainer"
    export AZSHARENAME="${PROJECT}-files-$PROJECTENV"

}

### should check if $AZRG is a group and if not create it
# example group create
az_create_group () 
{
    az group create --location $AZLOCATION --name $AZRG --tags $AZTAGS
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
    az acr build -g $AZRG -t $AZDOCKERIMAGE:$TAG -r $AZCR .

    # alternative - AZCR task queue
    # echo "queue azue acr task that builds from a github repository."
    # echo "unless you have CI/CD/Git hooks configured, push to github first"
    # az acr task run -n build_$AZDOCKERIMAGE -r $AZCR -c <github url> -f Dockerfile

    az acr repository list -n $AZCR
    read -n1 -r -p "is the image $AZDOCKERIMAGE on this list? Press n to exit script" key
    if [ "$key" = 'n' ]; then
        echo "repository error, exiting"
        return 1
    fi
}

##########
# az_git_deployment_set ()
# {

# }

# az_git_deployment_url ()
# {

# }


az_create_webapp ()
{
    echo "Make a web app using custom dockerfile"
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
    # https://docs.microsoft.com/en-us/azure/app-service/scripts/cli-deploy-local-git?toc=/cli/azure/toc.json
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
    # this doesn't seem to create a new identity if one exists, just returns existing identity UUID
    export AZAPPIDENTITY=$(az webapp identity assign --resource-group $AZRG --name $AZAPPNAME --query principalId --output tsv)
    

    # git deployment of code (not container)
    # the container does not contain the python code, that gets deployed to standard folder on the app service "machine"
    ## to access the storage, the app needs an "identity"  


    az webapp deployment source config-local-git \
        -g $AZRG -n $AZAPPNAME


}


az_get_app_identity() {
    az webapp identity show --resource-group $AZRG --name $AZAPPNAME --query principalId --output tsv

}


az_git_setup ()
{
echo "your azure deployment user is:"
    
    AZREMOTENAME=azure
    AZGITREMOTE=https://AZGITUSERNAME@$AZAPPNAME.scm.azurewebsites.net/$AZAPPNAME.git
    # TODO test if the current azure remote is the same, then no need to delete and re-add

    # in this folders git comit, 
    echo "updating yuor git remotes for azure deploy "
    echo "removing existing remote $AZREMOTENAME"
    git remote remove $AZREMOTENAME
    echo "adding azure git remote $AZREMOTENAME as $AZGITREMOTE"
    git remote add $AZREMOTENAME $AZGITREMOTE
    echo "your next step is to run command:"
    echo "git push $AZREMOTENAME master"
    echo "using the deployment password you've set. "

    ## NEXT 
    # the dockerfile does not contain the app scripts, only software to run it
    # use the portal to set your userid and password for "local git deploy",
    # and portal to copy/paste the deployment git URL, 
    # add that remote to your app repository and push
}

## set application-level configuration using a env file from this repository

az_webapp_setconfig ()
{
    # read the file $ENVFILE, and convert to space delimited set of values
    AZ_ENV_VARS=`paste -sd " " $ENVFILE`
    # set the values from the ENVFILE in the webapp
    cmd="az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings WEBSITES_PORT=$PORT $AZ_ENV_VARS"
    echo $cmd
    $(cmd)

    az_app_restart
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
    echo "using azure $AZCR to build the files in this repository"
    az acr build -t $AZDOCKERIMAGE:$TAG -r $AZCR .
}


# this will set/reset the image to be used for the container for the web app
# the container is initially set above when the web app is created
# run this if you update the container , or need to use a different image:tag name
az_app_set_container ()
{
   az webapp config container set --name $AZAPPNAME --resource-group $AZRG --docker-custom-image-name ${AZCR}.azurecr.io/$AZDOCKERIMAGE:$TAG --docker-registry-server-url https://${AZCR}.azurecr.io
   # this setting gets set to false sometimes, so set to true AGAIN here 
   az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
   # is manual restart needed, or is it auto-restarted when config is changed?
   az_app_restart

}


# WIP
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

az_create_container_instance ()
{
# users the Azure Containers Instances instead of App Service
az container create -g $AZRG --name $AZAPPNAME \
    --ports 80 443 8000 22 2222 --ip-address Public \
    --image $AZCR.azurecr.io/$AZDOCKERIMAGE:$TAG \
    --registry-username $AZCR \
    --registry-password $(az acr credential show --name $AZCR -g $AZRG  --output tsv  --query="passwords[0]|value") 
    #     --dns-name-label $AZAPPNAME

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

az_create_file_storage ()
{

export AZSTORAGESKU="Premium_LRS"

# cheaper options 
# SKU=Standard_LRS
az storage account create -g $AZRG --name $AZSTORAGENAME -l $AZLOCATION \
    --sku $AZSTORAGESKU --kind FileStorage \
    --tags $AZTAGS

export AZSTORAGEKEY=$(az storage account keys list -g $AZRG -n $AZSTORAGENAME --query [0].value -o tsv)

az storage share create --account-name  $AZSTORAGENAME --name $AZSHARENAME --account-key $AZSTORAGEKEY --enabled-protocol SMB 

## to access the storage, the app needs an "identity"  
# move to az web app create
# AZAPPIDENTITY=$(az webapp identity assign --resource-group $AZRG --name $AZAPPNAME --query principalId --output tsv)

# TODO send command to app service to create this mount folder
MOUNTPATH=/home/site/$AZSHARENAME

# NOTE to simply make a change to the path that is mounted, use 
# az webapp config storage-account update -g $AZRG -n $AZAPPNAME \
#   --custom-id $AZAPPIDENTITY \
#   --mount-path $MOUNTPATH
# add a new mount
az webapp config storage-account add --resource-group $AZRG \
    --name $AZAPPNAME \
    --custom-id $AZAPPIDENTITY \
    --storage-type AzureFiles \
    --share-name $AZSHARENAME \
    --account-name $AZSTORAGENAME --access-key $AZSTORAGEKEY \
    --mount-path $MOUNTPATH
}

###### tell the app to use the file storage just created

az_update_file_storage()
{
az webapp config storage-account update -g $AZRG -n $AZAPPNAME \
  --custom-id $AZAPPIDENTITY \
  --mount-path $MOUNTPATH
}


az_storage_endpoint_info() {
    httpEndpoint=$(az storage account show \
    --resource-group $AZRG \
    --name $AZSTORAGENAME \
    --query "primaryEndpoints.file" | tr -d '"')

    smbPath=$(echo $httpEndpoint | cut -c7-$(expr length $httpEndpoint))
    echo "$AZSTORAGENAME samba path = $smbPath"

    fileHost=$(echo $smbPath | tr -d "/")
    echo "$AZSTORAGENAME  filehost = $fileHost"


}


#############
# APP DATABASE CREATION
# this strategy bundles the data server with the app creation code and resource group
# which is easier to manage per-project but not per-server
az_app_database_create () 
{

    # Create a PostgreSQL server with a single database instance
    # for this project in the same Resource Group
    # uses  variables defined above eg resource group $AZRG 
    # Name of a server maps to DNS name and is thus required to be globally unique in Azure.
    # Substitute the <server_admin_password> with your own value.


    # PARAMETERS
    AZDBSERVERNAME=${PROJECT}-psql
    DB_NAME=$AZAPPNAME-dev
    DB_ADMIN_NAME=${PROJECT}admin
    # set the server SKU if it is not set already 
    AZDBSKU="${AZDBSKU:-B_GEN5_1}"  # default to small database, basic gen5 1 CPUS  --sku_name
    DBSTORAGE=$((5120+(5*1024)))   # in megabytes --storage_size. min is 5120 10gb => 10250

    # docs for SKU and storage for postgresql on azure
    # https://docs.microsoft.com/en-us/azure/postgresql/quickstart-create-server-database-azure-cli#create-an-azure-database-for-postgresql-server

    # TODO check if db server exists first 
    # TODO check if db exists on that server, requires firewall access to that db from current pc

    echo "creates project database server called $SERVER_NAME in group $AZRG with admin ID $DB_ADMIN_NAME"
    read -p "Enter new password for $DB_ADMIN_NAME (no quote marks please) or ctrl+c to cancel...  " DB_ADMIN_PW

    if [[ -z "$DB_ADMIN_PW" ]]; then
        "No password entered, exiting"
        return 1
    else  
        read -p "confirm password" DB_ADMIN_PW_CONFIRM
        if [[ "$DB_ADMIN_PW" != "$DB_ADMIN_PW_CONFIRM" ]]; then
            echo "passwords don't match, exiting, sorry"    
            return 1
        fi
    fi

    #TODO add tag created_by=$USER

    az postgres server create \
    --name  $AZDBSERVERNAME \
    --resource-group $AZRG \
    --location $AZLOCATION \
    --admin-user $DB_ADMIN_NAME \
    --admin-password $DB_ADMIN_PW \
    --sku-name $AZDBSKU \
    --storage-size $DBSTORAGE \
    --auto-grow Enabled


    # Configure a firewall rule for the server

    echo "opening firewall to MSU wired connections"
    az postgres server firewall-rule create \
    --resource-group $AZRG \
    --server $AZDBSERVERNAME \
    --name allow_msu_wired_358 \
    --start-ip-address 35.10.0.0 \
    --end-ip-address 35.10.255.255

    read -p "Enter your IP to open or blank to skip... " IP_FOR_ACCESS

    if [[ -z "$IP_FOR_ACCESS" ]]; then
        "No IP entered"

    else  
    az postgres server firewall-rule create \
    --resource-group $AZRG \
    --server $AZDBSERVERNAME \
    --name first_allowed_single_IP \
    --start-ip-address $IP_FOR_ACCESS \
    --end-ip-address $IP_FOR_ACCESS

    echo "opened up $SERVER_NAME for $IP_FOR_ACCESS"
    fi

    echo creating $DB_NAME on $AZDBSERVERNAME
    az postgres db create \
        --name $DB_NAME \
        --resource-group $AZRG \
        --server $AZDBSERVERNAME \

    echo "If there were no errors, the database was created.  "
    echo "a psql connection command is (without the password)"
    echo "psql -h $SERVER_NAME.postgres.database.azure.com -U ${DB_ADMIN_NAME}@$SERVER_NAME  $DB_NAME"

    # todo check if azure app service is created, then can set the connection string
    # when that check is in, can add the connection string setting here...
    # az_app_set_dburi

    }

az_app_set_dburi ()
{
    echo "setting the app service DB URI configuration using standard db names. "
    # afer the database and app are created, 
    # set the connection string of the app
    # this makes a lot of assumptions about how the app is configured: 
    # 1) the app has been provisioned already, before the database is (not alwasy true)
    # 2) the app uses python sqlalchemy
    # 3) the app config env variable is SQLALCHEMY_DATABASE_URI
    # 4) and that the app configuration reads from environment variables
    AZDBSERVERNAME=${PROJECT}-psql
    DB_NAME=$AZAPPNAME-dev
    DB_ADMIN_NAME=${PROJECT}admin
    # user enters pw from command line
    read -p "Enter password you entered when creating $DB_NAME for $DB_ADMIN_NAME (no quote marks please) or ctrl+c to cancel...  " DB_ADMIN_PW

    APPDBCONN=postgresql://${DB_ADMIN_NAME}%40${AZDBSERVERNAME}:${DB_ADMIN_PW}@${AZDBSERVERNAME}.postgres.database.azure.com:5432/$DB_NAME

    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME \
    --settings SQLALCHEMY_DATABASE_URI=$APPDBCONN
}

az_app_database_delete () 
{
    AZDBSERVERNAME=$PROJECT-psql
    DB_NAME=$AZAPPNAME-dev

    echo "Deleting PG Server $AZDBSERVERNAME and all data on it"
    az postgres server delete --resource-group $AZRG \
        --name $SERVER_NAME \

}


az_set_app_hostname ()
{
    # TODO check that an argument was set

if [[ -z "$1" ]]; then
    "No     hostname provided, exiting"
else  
    az webapp config hostname add \
    --webapp-name $AZAPPNAME --resource-group $AZRG \
    --hostname $1

    echo "try browsing http://${fqdn} to see $AZAPPNAME"
fi
}

