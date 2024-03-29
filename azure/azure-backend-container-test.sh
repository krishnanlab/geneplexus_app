## BACK-END CONTAINER TEST
# these CLI commands mimic what our logic-app
# should do create an Azure Container Instance from a container
# along with some commands to build the container
# requirements
# resource group, storage account already created for this test env
## to run the test
## from the project root folder in bash shell...
#
# . azure/azure-backend-container-test.sh
# . azure/azuredeploy.sh
# az_set_vars test   # AZDOCKERIMAGE, AZRG, AZCR, TAG, etc
##  build everything in this new test env, if it isn't already , especially az_build_docker_backend
# set_backend_vars
# run_geneplexus_container testjob-$RANDOM
## look into the storage account for output files 

set_backend_vars () 
{
  export BACKEND_IMAGE=${AZDOCKERIMAGE}-backend
  # TAG is set in azuredeploy.sh
  export AZDOCKERCONTAINERNAME=${BACKEND_IMAGE}-$RANDOM
  export AZBACKENDIMAGE_URL=$ACR.azurecr.io/$BACKEND_IMAGE:$TAG
  export DOCKERFILE="Dockerfile-backend"  # the name of the file in this project

  # MODIFY THIS IF THIS FOLDER CHANGES
  export BACKEND_DATA_FOLDER=data_backend2
}

###### TEST RUN
# manually set the env vars, provision and run an azure container instance
# for the application, we use an az logic app to do this for us
run_geneplexus_container ()
{

# PARAMS: use param for jobname, input file name but otherwise this is geared for running the geneplexus backend docker container
JOBNAME=${1:-testjob}
GENE_FILE_NAME=${2:-input_genes.txt}


SKEY=$(get_storage_key $AZSTORAGENAME)
CONTAINER_MOUNT_PATH=/home/dockeruser/$AZSHARENAME

# setting memory could be done depending on the size of the network
MEMORY_NEEDED=4.0

# create local file to hold env vars
# WORKDIR=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
# LOCAL_ENV_VARS_FILE=$WORKDIR/dockerenv
# touch $LOCAL_ENV_VARS_FILE

CONTAINER_ENV_VARS=""
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS FLASK_ENV=development"
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS FLASK_DEBUG=TRUE" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS GP_NET_TYPE=BioGRID" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS GP_FEATURES=Embedding" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS GP_GSC=GO" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS JOBNAME=${JOBNAME}"
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS DATA_PATH=$CONTAINER_MOUNT_PATH/$BACKEND_DATA_FOLDER/"  # must have trailing slash
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS JOB_PATH=$CONTAINER_MOUNT_PATH/jobs/" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS GENE_FILE=$JOB_PATH/${JOBNAME}/input_genes.txt" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS OUTPUT_FILE=$JOB_PATH/${JOBNAME}/results.html" 

echo "ENV VARS = $CONTAINER_ENV_VARS"

AZ_ACR_PW=$(az acr credential show --name $ACR -g $AZRG  --output tsv  --query="passwords[0]|value")

# ref https://docs.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az_container_create

echo "creating container instance ${AZDOCKERCONTAINERNAME}"
echo "pulling from ${AZBACKENDIMAGE_URL}"
az container create \
  --resource-group $AZRG \
  --name ${AZDOCKERCONTAINERNAME} \
  --image ${AZBACKENDIMAGE_URL} \
  --registry-username $ACR \
  --registry-password $AZ_ACR_PW \
  --location $AZLOCATION \
  --os-type Linux \
  --memory $MEMORY_NEEDED
  --restart-policy Never \
  --environment-variables $CONTAINER_ENV_VARS \
  --azure-file-volume-account-key $SKEY \
  --azure-file-volume-account-name $AZSTORAGENAME \
  --azure-file-volume-mount-path $CONTAINER_MOUNT_PATH \
  --azure-file-volume-share-name $AZSHARENAME
  --tags project=$PROJECT


# this should create instance, pull the container, run the instance, which saves a file to $OUTPUT_FILE from the $CONTAINER_ENV_VARS list


echo "container status"
az container show \
  --resource-group $AZRG \
  --name ${AZDOCKERCONTAINERNAME} \
  --query containers[0].instanceView.currentState.state

az container logs \
  --resource-group $AZRG \
  --name ${AZDOCKERCONTAINERNAME}

# I'm guessing on this one
az container delete \
  --resource-group $AZRG \
  --name ${AZDOCKERCONTAINERNAME} \

# echo "getting container FQDN (may not be used for batch containers"
# az container show \
#   --resource-group $AZRG \
#   --name $AZCONTAINERNAME \
#   --query "{FQDN:ipAddress.fqdn,ProvisioningState:provisioningState}" \
#   --out table

}

# tutorial on getting data about how a container has run
# https://docs.microsoft.com/en-us/learn/modules/run-docker-with-azure-container-instances/6-troubleshoot-aci
# 

get_container_id ()
{
  az container show \
  --resource-group $AZRG \
  --name $1 \
  --query id \
  --output tsv
}

az_get_container_data () 
{

CONTAINER_ID=$(get_container_id $AZCONTAINERNAME)

THIS_CONTAINER_CPU_METRICS=$(az monitor metrics list \
  --resource $CONTAINER_ID \
  --metric CPUUsage \
  --output table)

THIS_CONTAINER_MEMORY_METRICS=$(az monitor metrics list \
  --resource $CONTAINER_ID \
  --metric MemoryUsage \
  --output table)

THIS_CONTAINER_LOGS=$(az container logs \
  --resource-group $AZRG \
  --name $AZCONTAINERNAM
)

# write THIS_CONTAINER_METRICS and to with job output  filename=${JOB_NAME}_METRICS, same for logs
# 

}

### this is the example code I started from form Azure 
# I actually don't know where I got it from... 
# but here is another example, although written with TerraForm  and not the CLI! 
#https://docs.microsoft.com/en-us/azure/developer/terraform/deploy-azure-cosmos-db-to-azure-container-instances

containerdbdemo () 
{

AZCONTAINERNAME=${APPNAME}-$RANDOM


COSMOS_DB_NAME=aci-cosmos-db-$RANDOM
echo "creating databbase for container  $COSMOS_DB_NAME"

COSMOS_DB_ENDPOINT=$(az cosmosdb create \
  --resource-group $AZRG \
  --name $COSMOS_DB_NAME \
  --query documentEndpoint \
  --output tsv)

COSMOS_DB_MASTERKEY=$(az cosmosdb keys list \
  --resource-group $AZRG \
  --name $COSMOS_DB_NAME \
  --query primaryMasterKey \
  --output tsv)

echo "creating container $AZCONTAINERNAME"
az container create \
  --resource-group $AZRG \
  --name $AZCONTAINERNAME \
  --image microsoft/azure-vote-front:cosmosdb \
  --ip-address Public \
  --location $AZLOCATION \
  --secure-environment-variables \
    COSMOS_DB_ENDPOINT=$COSMOS_DB_ENDPOINT \
    COSMOS_DB_MASTERKEY=$COSMOS_DB_MASTERKEY


az container show \
  --resource-group $AZRG \
  --name $AZCONTAINERNAME \
  --query ipAddress.ip \
  --output tsv
}


# alternate code for creating a container instance...

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


# connecting to azure storage from a container
# 1) use managed identities https://docs.microsoft.com/en-us/azure/container-instances/container-instances-managed-identity

# triggering from azure function
# https://docs.microsoft.com/en-us/azure/container-instances/container-instances-tutorial-azure-function-trigger
