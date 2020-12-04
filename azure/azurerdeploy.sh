# Azure Container Registry
# ===
# bash script to show how to use the Azure Container Registry (ACR) with AppService
# using Azure CLI
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
#   * a configuration file named .azenv in same format as the usual .env
#      - the .env file in your directory is not copied into the docker container
#      - the .azenv file is for azure webapp 'appsettings' which translate to env vars in th container
# OPTIONAL
#   * Docker installed

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

    # variables

    # TODO introduce a department name here, and prefix other names with that, and use for the ACR
    export IMAGE=geneplexus # TODO => rename to AZDOCKERIMAGE
    export PROJECT=krishnanlabgeneplexus
    export RG=ADS${PROJECT}Dev

    # note from microsoft about A container registry names: 
    # Uppercase characters are detected in the registry name. When using its server url in docker commands, to avoid authentication errors, use all lowercase.

    export ACR=${PROJECT}acr  # this could be better_named, or a department-wide ACR 

    export PLAN=${PROJECT}_serviceplan
    export APPNAME=geneplexus
    export AZLOCATION=northcentralus
    export ENVFILE=azure/.azenv
    export AZTAGS="createdby=$USER" # project=$PROJECT" # this is not the right syntax to set multiple tags in one go
    export AZ_SERVICE_PLAN_SKU="P2v2"  # "S1"  # see https://azure.microsoft.com/en-us/pricing/details/app-service/linux/
    # apps like gunicorn or DJango run on port 8000
    # if you are testing a flask app dev server, change this to 5000
    # but don't use flask app dev server for production!
    export PORT=8000
    export TAG=latest  # TODO => rename to AZDOCKERTAG
}

### should check if $RG is a group and if not create it
# example group create
az_create_group () 
{
    az group create --location $AZLOCATION --name $RG --tags "$AZTAGS"
}

#########
## build)   
## TODO check if a registry exists and if not build it
az_create_app_registry()
{
    echo "MAKE A REGISTRY $ACR in group $RG"
    az acr create --name $ACR --resource-group $RG --sku Basic --admin-enabled true
    # we need a password from the ACR for other steps
    # this uses the Azure CLI JMSEpath and TSV ouutput to extract the first of two passwords
    # note this has been replaced by used of stdin password below
    # acrpw=`az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value"`

    # always build, assume running to rebuild
    ## TODO remove existing Image in the ACR first?
    echo "using azure acr to build the files in this repository"
    az acr build -g $RG -t $IMAGE:$TAG -r $ACR .

    # alternative - ACR task queue
    # echo "queue azue acr task that builds from a github repository."
    # echo "unless you have CI/CD/Git hooks configured, push to github first"
    # az acr task run -n build_$IMAGE -r $ACR -c <github url> -f Dockerfile

    ###
    # buildlocal)  or build --local
    # alternative - use local docker, build locally, docker login and docker push  to Azure
    # this requires a docker installation, built image, and good upstream bandwidth 
    # build the image first with the build_biosci_docker() function below
    #echo "DOCKER LOGIN AND PUSH IMAGE TO REGISTRY"
    # for the Azure ACR, the username is the ACR name
    #az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value" | \
    #docker login $ACR.azurecr.io --username $ACR  --password-stdin 

    # should check that login is successful  $@ or $?  
    # not sure why you have to re-tag the image with the repo name in it?
    # docker tag $IMAGE:$TAG $ACR.azurecr.io/$IMAGE:$TAG
    # docker push $ACR.azurecr.io/$IMAGE:$TAG
    # get some coffee, this will take a while
    # then check it! 

    az acr repository list -n $ACR
    read -n1 -r -p "is the image $IMAGE on this list? Press n to exit script" key
    if [ "$key" = 'n' ]; then
        echo "repository error, exiting"
        return 1
    fi
}

##########

az_create_webapp ()
{
    echo "Make a web app"
    # requirements: working Dockerfile, created resource group and ACR in that group
    # also reads a local .azenv file
    # make an app,  and tell it about the registry
    az appservice plan create --name $PLAN --resource-group $RG --location $AZLOCATION --number-of-workers 2 --sku $AZ_SERVICE_PLAN_SKU --is-linux --tags "$AZTAGS"

    # commands to use a container registry that requires credentrials - not neeed for an ACR in the same subscription
    # export AZ_ACR_PW=$(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")
    # az webapp create -g $RG -p $PLAN -n $APPNAME --tags "$AZTAGS" \
            # --deployment-container-image-name $ACR.azurecr.io/$IMAGE:$TAG  \
            # --docker-registry-server-user $ACR  \
            # --docker-registry-server-password $AZ_ACR_PW


    # CLI to create web app using custom container from 'local' Azure container repository (ACR)
    az webapp create -g $RG -p $PLAN -n $APPNAME --tags "$AZTAGS" \
            --deployment-container-image-name $ACR.azurecr.io/$IMAGE:$TAG  

    # TODO: see how to use these for for CI/CD from gitlab
                #  [--deployment-local-git]
                #  [--deployment-source-branch]
                #  [--deployment-source-url]

    # Azure documentation say this is on by default, but that's a lie.  You must turn it on manually like this
    # this allows the /home/site/wwwroot folder to be mounted into the custom container 
    az webapp config appsettings set --resource-group $RG --name $APPNAME --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true

    # note - setting the docker image from ACR in this way fails the log-in
    # use the method below to send a password 
    #  -i $ACR.azurecr.io/$IMAGE:$TAG 
    # this assumes there is a file with the name you set the variable $ENVFILE above 
    # that contains config values for flask to run in Azure
    # and this command translates a .env file with a space-seperated list for az cli
    AZ_ENV_VARS=`paste -sd " " $ENVFILE`

    # note settings in format VAR=VALUE and the parameter is not quoted for the is command (unlike tags)
    az webapp config appsettings set --resource-group $RG \
            --name $APPNAME \
            --settings WEBSITES_PORT=$PORT $AZ_ENV_VARS

    az webapp log config --name $APPNAME \
            --resource-group $RG \
            --application-logging  filesystem \
            --docker-container-logging filesystem \
            --level information

    ## NEXT 
    # the dockerfile does not contain the app scripts, only software to run it
    # use the portal to set your userid and password for "local git deploy",
    # and portal to copy/paste the deployment git URL, 
    # add that remote to your app repository and push

}

az_browse_webapp () 
{
    # does it work?  
    # It takes a good 5 minutes to copy the container from ACR to app service
    # you could also check on  the Azure portal for your resoruce group, 
    # there is is a button for container logs
    open http://$APPNAME.azurewebsites.net

    # also try to access the control panel for this 
    open http://$APPNAME.scm.azurewebsites.net
}

az_build_container ()
{
    echo "using azure $ACR to build the files in this repository"
    az acr build -t $IMAGE:$TAG -r $ACR .
}

az_app_set_container ()
{
   az webapp config container set --name $APPNAME --resource-group $RG --docker-custom-image-name ${ACR}.azurecr.io/$IMAGE:$TAG --docker-registry-server-url https://${ACR}.azurecr.io 
}

az_app_stage ()
{
    # TODO remove this and use the build function
    #echo "using azure acr to build the files in this repository"
    #az acr build -t $IMAGE:$TAG -r $ACR .

    az_build_container

    SLOTNAME=staging

    az webapp deployment slot delete  --name $APPNAME  \
            --resource-group $RG  \
            --slot $SLOTNAME \

   # create "slot for staging and copy from the 
    az webapp deployment slot create --name $APPNAME  \
            --resource-group $RG  \
            --slot $SLOTNAME \
            --configuration-source $APPNAME

    az_app_set_container

    # preview (works on mac)
    open http://${APPNAME}.azurewebsites.net/?x-ms-routing-name=${SLOTNAME}

}


az_app_set_production_container () 
{
        az webapp config container set --name $APPNAME  \
            --resource-group $RG  \
            --docker-custom-image-name $ACR.azurecr.io/$IMAGE:$TAG  \
            --docker-registry-server-url https://$ACR.azurecr.io  \
            --docker-registry-server-user $ACR  \
            --docker-registry-server-password $(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")
}

az_app_update_container () 
{
    # rebuild from the docker file on the Azue ACR
    # and then update the app to use this new container
    ### NOTE this doesn't update the c
    az_build_container
    az_app_set_container
}

az_app_restart () 
{
    az webapp restart --name $APPNAME -g $RG
}
## NOTE previous
az_app_update ()
{
    # function to only update the application when the vars have been set
    # if the RG, registry, app service plan, and app service have all been created, 
    # then all that needs doing is to rebuild the container (assumes the Dockerfile is good
    # for a valid build) and update the container config for the web app
    # and restart the web application

    az_build_container

    az webapp config container set --name $APPNAME  \
            --slot $
            --resource-group $RG  \
            --docker-custom-image-name $ACR.azurecr.io/$IMAGE:$TAG  \
            --docker-registry-server-url https://$ACR.azurecr.io  \
            --docker-registry-server-user $ACR  \
            --docker-registry-server-password $(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")

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
    docker build --tag $IMAGE:$TAG .

    docker images 
    read -n1 -r -p "Did the docker image build? Pres 'n' to exit script" key

    if [ "$key" = 'n' ]; then
        echo "docker couldnt' build app, exiting"
        return 1
    fi


    ### TEST that the dockerfile can run and works locally (optional)
    echo "running application and opening browser..."
    # this requires a file to hold the environment variables for running locally
    docker run -d -p ${PORT}:${PORT} --env-file .dockerenv --name ${IMAGE}_container $IMAGE:$TAG
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

    echo "this deletes ALL the things related to app $APPNAME app, plan, repo"
    echo "this doesn't delete the database, but does delete all files,logs etc from app VM"
    echo "deleting app $APPNAME"
    az webapp delete --resource-group $RG --name $APPNAME
    echo deleting appservice $PLAN
    az appservice plan delete --resource-group $RG --name $PLAN

}

az_acr_image_delete ()
{
    echo deleting docker image $IMAGE:$TAG from $ACR

    # note if you just want to replace the latest image, 
    #you can delete just one tagged image of the repository
    az acr repository delete --name $ACR --repository  $IMAGE

}

az_acr_delete ()
{
    echo deleting repository $ACR
    az acr delete --resource-group $RG --name $ACR 

}

az_local_docker_teardown ()
{
    echo deleting docker image $IMAGE:$TAG
    docker rmi $IMAGE
    docker rmi $IMAGE:$TAG
}

az_create_container_instance ()
{
# users the Azure Containers Instances instead of App Service
az container create -g $RG --name $APPNAME \
    --ports 80 443 8000 22 2222 --ip-address Public \
    --image $ACR.azurecr.io/$IMAGE:$TAG \
    --registry-username $ACR \
    --registry-password $(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value") 
    #     --dns-name-label $APPNAME

}

#################
# storage account 
# this is used for mounting files to the web application to access large files
# so that they do not go into the container itself or sit on the web app

az_create_blob_storage ()
{
export AZSTORAGESKU="Premium_LRS"
export AZSTORAGENAME="${APPNAME}bobstorage"
export AZCONTAINERNAME="${APPNAME}files"

az storage account create -g $RG --name $AZSTORAGENAME -l $AZLOCATION \
    --sku $AZSTORAGESKU --kind BlobStorage \
    --tags $AZTAGS
}
az_create_file_storage ()
{

export AZSTORAGESKU="Premium_LRS"
export AZSTORAGENAME="${APPNAME}storage"
export AZSHARENAME="${APPNAME}files"
# cheaper options 
# SKU=Standard_LRS
az storage account create -g $RG --name $AZSTORAGENAME -l $AZLOCATION \
    --sku $AZSTORAGESKU --kind FileStorage \
    --tags $AZTAGS

export AZSTORAGEKEY=$(az storage account keys list -g $RG -n $AZSTORAGENAME --query [0].value -o tsv)

az storage share create --account-name  $AZSTORAGENAME --name $AZSHARENAME --account-key $AZSTORAGEKEY --enabled-protocol SMB 

## to create the storage, the app needs an "identity"  

AZAPPIDENTITY=$(az webapp identity assign --resource-group $RG --name $APPNAME --query principalId --output tsv)

az webapp config storage-account add --resource-group $RG \
    --name $APPNAME \
    --custom-id $AZAPPIDENTITY \
    --storage-type AzureFiles \
    --share-name $AZSHARENAME \
    --account-name $AZSTORAGENAME --access-key $AZSTORAGEKEY \
    --mount-path /mnt

az webapp config storage-account add --resource-group $RG \
    --name $APPNAME \
    --custom-id $AZAPPIDENTITY \
    --storage-type AzureFiles \
    --share-name $AZSHARENAME \
    --account-name $AZSTORAGENAME --access-key $AZSTORAGEKEY \\
}
 

# todo fix this (it doesn't work)
# see https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-files
az_copy_hpcc_to_files ()
{
    SOURCEFOLDER=$1 
    # TODO check that a source folder was sent!!!

    AZSTORAGENAME="${APPNAME}storage"
    AZSHARENAME="${APPNAME}files"

    # for blob storage, doesn't work for Azure files
    # AZSTORAGEKEY=$(az storage account keys list -g $RG -n $AZSTORAGENAME --query [0].value -o tsv)

    # for azure files
    # this assumes the identity was set
    # TODO check if an identity is actually set, and if not, set one
    AZAPPIDENTITY=$(az webapp identity show --resource-group $RG --name $APPNAME --query principalId --output tsv)
    AZSTORAGEURL="https://${AZSTORAGENAME}.file.core.windows.net/${AZSHARENAME}?${AZSASTOKEN}"
    
    COPY_CMD="azcopy copy $SOURCEFOLDER $AZSTORAGEURL --recursive"
    ssh hpcc $CMD
}

#############
# APP DATABASE CREATION

az_create_app_database () 
{

# Create a PostgreSQL server for this project in the same Resourcve Group
# uses  variables defined above eg resource group $RG 
# Name of a server maps to DNS name and is thus required to be globally unique in Azure.
# Substitute the <server_admin_password> with your own value.


# PARAMETERS
SERVER_NAME=${PROJECT}db
DB_NAME=$APPNAME
DB_ADMIN_NAME=${PROJECT}admin
DB_SKU=B_GEN5_2  # small database, basic gen5 2 CPUS  --sku_name
DB_STORAGE=$((5120+(5*1024)))   # in megabytes --storage_size. min is 5120 10gb => 10250

# docs for SKU and storage for postgresql on azure
# https://docs.microsoft.com/en-us/azure/postgresql/quickstart-create-server-database-azure-cli#create-an-azure-database-for-postgresql-server

# TODO check if db server exists first 
# TODO check if db exists on that server, requires firewall access to that db from current pc

echo "creates project database server called $SERVER_NAME in group $RG with admin ID $DB_ADMIN_NAME"
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
--name  $SERVER_NAME \
--resource-group $RG \
--location $AZLOCATION \
--admin-user $DB_ADMIN_NAME \
--admin-password $DB_ADMIN_PW \
--sku-name $DB_SKU \
--storage-size $DB_STORAGE \
--auto-grow Enabled


# Configure a firewall rule for the server

echo "opening firewall to MSU wired connections"
az postgres server firewall-rule create \
--resource-group $RG \
--server $SERVER_NAME \
--name allow_msu_wired_358 \
--start-ip-address 35.10.0.0 \
--end-ip-address 35.10.255.255

read -p "Enter your IP to open or blank to skip... " IP_FOR_ACCESS

if [[ -z "$IP_FOR_ACCESS" ]]; then
    "No IP entered"

else  
az postgres server firewall-rule create \
--resource-group $RG \
--server $SERVER_NAME \
--name first_allowed_single_IP \
--start-ip-address $IP_FOR_ACCESS \
--end-ip-address $IP_FOR_ACCESS

echo "opened up $SERVER_NAME for $IP_FOR_ACCESS"
fi

echo creating $DB_NAME on $SERVER_NAME
az postgres db create \
    --name $DB_NAME \
    --resource-group $RG \
    --server $SERVER_NAME \

echo "If there were no errors, the database was created.  "
echo "a psql connection command is (without the password)"
echo "psql -h $SERVER_NAME.postgres.database.azure.com -U ${DB_ADMIN_NAME}@$SERVER_NAME  $DB_NAME"
echo "use Azure cloud shell to import/restore a dump file into this new db"

}

az_set_app_hostname ()
{
    # TODO check that an argument was set

if [[ -z "$1" ]]; then
    "No     hostname provided, exiting"
else  
    az webapp config hostname add \
    --webapp-name $APPNAME --resource-group $RG \
    --hostname $1

    echo "try browsing http://${fqdn} to see $APPNAME"
fi
}

