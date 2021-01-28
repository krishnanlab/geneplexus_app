#!/usr/bin/env bash

# Create Azure Azure Services for app 
# ===
# bash script to show how to use the Azure Container Registry (ACR) with AppService
# using Azure CLI
# based on  https://docs.microsoft.com/en-us/azure/app-service/containers/tutorial-custom-docker-image


#REQUIREMENTS
# ---
#   * an Azure account in which you can create objects
#   * bash.  This script was tested on MacOS.  If on linux, ignore the 'open' commands
#   * standard bash env variables $HOME and $USER
#   * Azure CLI installed (I installed via Miniconda into a conda environment) (see 'using the az cli' below)
#   * It assumes your Azure CLI is configured and logged in 
#   * a project with a Dockerfile and a web app 
#   * a configuration file named .azenv in same format as the usual .env
#      - the .env file in your directory is not copied into the docker container
#      - the .azenv file is for azure webapp 'appsettings' which translate to env vars in th container
#   * ensure the values in az_set_vars () function below are correct for this deployment

# see the README.md file in this azure folder for details on how to use this script. 


az_set_vars ()
{

    # variables

    # TODO introduce a department name here, and prefix other names with that, and use for the ACR
    export IMAGE=geneplexus # TODO => rename to AZDOCKERIMAGE
    export PROJECT=geneplexusdev
    export RG=${PROJECT}

    # note from microsoft about A container registry names: 
    # Uppercase characters are detected in the registry name. When using its server url in docker commands, to avoid authentication errors, use all lowercase.

    export ACR=${PROJECT}acr  # this could be better named, or use a subscription-wide ACR

    export PLAN=${PROJECT}_serviceplan
    export APPNAME=${PROJECT}_app
    export AZLOCATION=centralus
    export ENVFILE=azure/.azenv
    export AZTAGS="created_by=$USER" # project=$PROJECT" # this is not the right syntax to set multiple tags in one go
    export AZ_SERVICE_PLAN_SKU="S1"  # see https://azure.microsoft.com/en-us/pricing/details/app-service/linux/ P2v2 was use to actually run models
    # apps like gunicorn or DJango run on port 8000
    # if you are testing a flask app dev server, change this to 5000
    # but don't use flask app dev server for production!
    export PORT=8000
    export AZDOCKERTAG=latest  # 'tag used for Docker image naming.  

    export AZSTORAGENAME="${APPNAME}storage"
    export AZCONTAINERNAME="${APPNAME}storagecontainer"
    export AZSHARENAME="${APPNAME}files"

    check_az_group_exists

}

check_az_group_exists ()
{
    matching group=$(az group list --query "[?name=='$RG']")
    if [ -z "$searchres" ]
    then
        echo "Resource group $RG doesn't exist, use the az_group_create function or CLI command"
        echo "az group create --location $AZLOCATION --name $RG --tags \"$AZTAGS\""
        return 1
    else
        return 0
     
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
    check_az_group_exists 
    echo "MAKE A REGISTRY $ACR in group $RG"
    az acr create --name $ACR --resource-group $RG --sku Basic --admin-enabled true
    # we need a password from the ACR for other steps
    # this uses the Azure CLI JMSEpath and TSV ouutput to extract the first of two passwords
    # note this has been replaced by used of stdin password below
    # acrpw=`az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value"`

    # always build, assume running to rebuild
    ## TODO remove existing Image in the ACR first?
    echo "using azure acr to build the files in this repository"
    az acr build -g $RG -t $IMAGE:$AZDOCKERTAG -r $ACR .

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
    # docker tag $IMAGE:$AZDOCKERTAG $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG
    # docker push $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG
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
    check_az_group_exists 
    echo "creating an Azure 'app service plan' and an 'app service'"
    # requirements: working Dockerfile, created resource group and ACR in that group
    # also reads a local .azenv file
    # make an app,  and tell it about the registry
    az appservice plan create --name $PLAN --resource-group $RG --location $AZLOCATION --number-of-workers 2 --sku $AZ_SERVICE_PLAN_SKU --is-linux --tags "$AZTAGS"

    # commands to use a container registry that requires credentrials - not neeed for an ACR in the same subscription
    # export AZ_ACR_PW=$(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")
    # az webapp create -g $RG -p $PLAN -n $APPNAME --tags "$AZTAGS" \
            # --deployment-container-image-name $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG  \
            # --docker-registry-server-user $ACR  \
            # --docker-registry-server-password $AZ_ACR_PW


    # CLI to create web app using custom container from 'local' Azure container repository (ACR)
    az webapp create -g $RG -p $PLAN -n $APPNAME --tags "$AZTAGS" \
            --deployment-container-image-name $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG  

    # TODO: see how to use these for for CI/CD from gitlab
                #  [--deployment-local-git]
                #  [--deployment-source-branch]
                #  [--deployment-source-url]

    # Azure documentation say this is on by default, but that's a lie.  You must turn it on manually like this
    # this allows the /home/site/wwwroot folder to be mounted into the custom container 
    az webapp config appsettings set --resource-group $RG --name $APPNAME --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true

    # note - setting the docker image from ACR in this way fails the log-in
    # use the method below to send a password 
    #  -i $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG 
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

    echo "next steps:"
    echo "for this project, the dockerfile does not contain the app scripts, only software to run it"
    echo 'use the portal to set/obtain your userid and password for "local git deploy",'
    echo 'and portal to copy/paste the deployment git URL'
    echo 'git add remote azure add that remote to your app repository and push'

}

az_app_url ()
{
    echo "http://$APPNAME.azurewebsites.net"
}

az_build_container ()
{
    echo "using azure registry named $ACR to build and host the docker image.  Requires a working Dockerfile"
    az acr build -t $IMAGE:$AZDOCKERTAG -r $ACR .
}

az_app_set_container ()
{
   # for the existing web app service, set a custom container based on image name and tag env variables here
   # this is necessary when first creating the web app service, and then if the image name or tag are changed

   az webapp config container set --name $APPNAME --resource-group $RG --docker-custom-image-name ${ACR}.azurecr.io/$IMAGE:$AZDOCKERTAG --docker-registry-server-url https://${ACR}.azurecr.io
   # this setting gets set to false sometimes, so set to true AGAIN here 
   az webapp config appsettings set --resource-group $RG --name $APPNAME --settings WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
   # is manual restart needed, or is it auto-restarted when config is changed?
   az_app_restart

}


# this was needed at one point due to passwords on the ACR, but may not be needed now
az_app_set_production_container () 
{
        az webapp config container set --name $APPNAME  \
            --resource-group $RG  \
            --docker-custom-image-name $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG  \
            --docker-registry-server-url https://$ACR.azurecr.io  \
            --docker-registry-server-user $ACR  \
            --docker-registry-server-password $(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")
}

az_app_update_container () 
{
    # rebuild from the docker file on the Azue ACR
    # and then update the app to use this new container
    ### NOTE this doesn't update the code that has been deployed via local git
    az_build_container
    az_app_set_container
}

az_app_restart () 
{
    az webapp restart --name $APPNAME -g $RG
}

az_app_update ()
{
    # function to only update the application when the vars have been set  or changed
    # this is not necessary for deploying updated code - that is done with git push 
    # if the RG, registry, app service plan, and app service have all been created, 
    # then all that needs doing is to rebuild the container (assumes the Dockerfile is good
    # for a valid build) and update the container config for the web app
    # and restart the web application

    az_build_container

    az webapp config container set --name $APPNAME  \
            --slot $
            --resource-group $RG  \
            --docker-custom-image-name $ACR.azurecr.io/$IMAGE:$AZDOCKERTAG  \
            --docker-registry-server-url https://$ACR.azurecr.io  \
            --docker-registry-server-user $ACR  \
            --docker-registry-server-password $(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")

    # not sure if this is necessary, or if config above will trigger a restart
    az webapp restart

}

# local Docker test
# does the docker file and app even work? if you have docker installed you caould build it and run it
# make sure you dont' have any other containers/apps running on localhost:8000
# if you've tried this before you may have to stop the container and rmi the image

az_local_docker_build ()
{
    # this is a function to use local docker installation to build local image for testing
    # this isn't needed for Azure deploy, just local testing
    docker build --tag $IMAGE:$AZDOCKERTAG .

    echo " if the build was sucesseful, then $IMAGE:$AZDOCKERTAG will be listed here: "
    docker images 
    echo "----"
    read -n1 -r -p "Did the docker image build? Pres 'n' to exit script" key

    if [ "$key" = 'n' ]; then
        echo "docker couldnt' build app, exiting"
        return 1
    fi


    ### TEST that the dockerfile can run and works locally (optional)
    echo "test running application and opening browser..."
    # this requires a file to hold the environment variables for running locally
    docker run -d -p ${PORT}:${PORT} --env-file .dockerenv --name ${IMAGE}_container $IMAGE:$AZDOCKERTAG
    open http://localhost:$PORT  # check it

}

az_app_delete ()
{
# Once you are done, tear it all down by running this function in the same terminal

    echo "this deletes ALL the things related to app $APPNAME app, plan, repo"
    echo "if you have copied or stored data on the app service disks, those files will be lost"
    echo "it will also delete all files,logs etc from app VM"
    read -n1 -r -p "Delete app? Press'y' to confirm " key

    echo "deleting app $APPNAME"
    if [ "$key" != 'y' ]; then
        echo "delete cancelled"
        return 1
    else
        az webapp delete --resource-group $RG --name $APPNAME
        echo deleting appservice $PLAN
        az appservice plan delete --resource-group $RG --name $PLAN

}

az_acr_image_delete ()
{
    echo "deleting docker image $IMAGE:$AZDOCKERTAG from $ACR"

    # note if you just want to replace the latest image, 
    #you can delete just one tagged image of the repository
    az acr repository delete --name $ACR --repository  $IMAGE

}

az_acr_delete ()
{
    echo "deleting repository $ACR"
    az acr delete --resource-group $RG --name $ACR 

}

az_local_docker_teardown ()
{
    # run this to clean up the test docker image
    echo "deleting docker image $IMAGE:$AZDOCKERTAG"
    docker rmi $IMAGE
    docker rmi $IMAGE:$AZDOCKERTAG
}


##############################
##### CREATE FILE STORAGE
# this application uses 
az_create_file_storage ()
{

export AZSTORAGESKU="Premium_LRS"

# cheaper options 
# SKU=Standard_LRS
az storage account create -g $RG --name $AZSTORAGENAME -l $AZLOCATION \
    --sku $AZSTORAGESKU --kind FileStorage \
    --tags $AZTAGS

export AZSTORAGEKEY=$(az storage account keys list -g $RG -n $AZSTORAGENAME --query [0].value -o tsv)

az storage share create --account-name  $AZSTORAGENAME --name $AZSHARENAME --account-key $AZSTORAGEKEY --enabled-protocol SMB 

## to access the storage, the app needs an "identity"  

AZAPPIDENTITY=$(az webapp identity assign --resource-group $RG --name $APPNAME --query principalId --output tsv)

# TODO send command to app service to create this mount folder
MOUNTPATH=/home/site/$AZSHARENAME

# NOTE to simply make a change to the path that is mounted, use 
# az webapp config storage-account update -g $RG -n $APPNAME \
#   --custom-id $AZAPPIDENTITY \
#   --mount-path $MOUNTPATH
# add a new mount
az webapp config storage-account add --resource-group $RG \
    --name $APPNAME \
    --custom-id $AZAPPIDENTITY \
    --storage-type AzureFiles \
    --share-name $AZSHARENAME \
    --account-name $AZSTORAGENAME --access-key $AZSTORAGEKEY \
    --mount-path $MOUNTPATH
}

az_update_file_storage()
{
az webapp config storage-account update -g $RG -n $APPNAME \
  --custom-id $AZAPPIDENTITY \
  --mount-path $MOUNTPATH
}


az_storage_endpoint_info() {
    httpEndpoint=$(az storage account show \
    --resource-group $RG \
    --name $AZSTORAGENAME \
    --query "primaryEndpoints.file" | tr -d '"')

    smbPath=$(echo $httpEndpoint | cut -c7-$(expr length $httpEndpoint))
    echo "$AZSTORAGENAME samba path = $smbPath"

    fileHost=$(echo $smbPath | tr -d "/")
    echo "$AZSTORAGENAME  filehost = $fileHost"


}

# DRAFT function that may be source'd on HPCC and run.
# this simply echos the command to run to copy and paste  
# see https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-files
az_copy_hpcc_to_files ()
{
    SOURCEFOLDER=$1 
    # TODO check that a source folder was sent!

    AZSTORAGENAME="${APPNAME}storage"
    AZSHARENAME="${APPNAME}files"

    # this option is for blob storage, doesn't work for Azure files
    # AZSTORAGEKEY=$(az storage account keys list -g $RG -n $AZSTORAGENAME --query [0].value -o tsv)

    # for azure files
    # this assumes the identity was set
    # TODO check if an identity is actually set, and if not, set one
    AZAPPIDENTITY=$(az webapp identity show --resource-group $RG --name $APPNAME --query principalId --output tsv)
    AZSTORAGEURL="https://${AZSTORAGENAME}.file.core.windows.net/${AZSHARENAME}?${AZSASTOKEN}"
    
    COPY_CMD="azcopy copy $SOURCEFOLDER $AZSTORAGEURL --recursive"
    ssh hpcc $CMD
}

az_set_app_hostname ()
{
# this is easier to do in the portal but here for completeness
if [[ -z "$1" ]]; then
    "No     hostname provided, exiting"
else  
    az webapp config hostname add \
    --webapp-name $APPNAME --resource-group $RG \
    --hostname $1

    echo "try browsing http://$1 to see $APPNAME"
fi
}

