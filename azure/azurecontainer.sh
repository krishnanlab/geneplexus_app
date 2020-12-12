source azure/azuredeploy.sh
# set ACR, etc
az_set_vars

#TODO  use variable 'suffix' to genericize 'backend' here
export AZDOCKERCONTAINERNAME=${IMAGE}-backend
export BACKEND_IMAGE=$AZDOCKERCONTAINERNAME
export AZBACKENDIMAGE_URL=$ACR.azurecr.io/$BACKEND_IMAGE:$TAG
export DOCKERFILE="Dockerfile-backend"

build_docker_backend ()
{
  az acr build -t $BACKEND_IMAGE:$TAG -r $ACR --file $DOCKERFILE .
}

get_storage_key()
{
  THIS_STORAGE_ACCOUNT=$1
  STORAGE_KEY=$(az storage account keys list --resource-group $RG --account-name $THIS_STORAGE_ACCOUNT --query "[0].value" --output tsv)
  echo $STORAGE_KEY
}



run_geneplexus_container ()
{


# DNS_NAME_LABEL=${APPNAME}-$RANDOM
# echo "using $DNS_NAME_LABEL"

# PARAMS: use param for jobname, input file name but otherwise this is geared for running the geneplexus backend docker container
JOBNAME=${1:-testjob}
GENE_FILE_NAME=${2:-input_genes.txt}


SKEY=$(get_storage_key $AZSTORAGENAME)
CONTAINER_MOUNT_PATH=/home/dockeruser/$AZSHARENAME

# setting memory could be done depending on the size of the network
$MEMORY_NEEDED=4.0

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
# add paths to env vars
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS DATA_PATH=$CONTAINER_MOUNT_PATH/data_backend" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS GENE_FILE=$CONTAINER_MOUNT_PATH/jobs/${JOBNAME}/input_genes.txt" 
CONTAINER_ENV_VARS="$CONTAINER_ENV_VARS OUTPUT_FILE=$CONTAINER_MOUNT_PATH/jobs/${JOBNAME}/results.html" 

echo "ENV VARS = $CONTAINER_ENV_VARS"

AZ_ACR_PW=$(az acr credential show --name $ACR -g $RG  --output tsv  --query="passwords[0]|value")

# ref https://docs.microsoft.com/en-us/cli/azure/container?view=azure-cli-latest#az_container_create

echo "creating container instance ${AZDOCKERCONTAINERNAME}"
echo "pulling from ${AZBACKENDIMAGE_URL}"
az container create \
  --resource-group $RG \
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
  --resource-group $RG \
  --name ${AZDOCKERCONTAINERNAME} \
  --query containers[0].instanceView.currentState.state

az container logs \
  --resource-group $RG \
  --name ${AZDOCKERCONTAINERNAME}

# I'm guessing on this one
az container delete \
  --resource-group $RG \
  --name ${AZDOCKERCONTAINERNAME} \

# echo "getting container FQDN (may not be used for batch containers"
# az container show \
#   --resource-group $RG \
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
  --resource-group $RG \
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
  --resource-group $RG \
  --name $AZCONTAINERNAM
)

# write THIS_CONTAINER_METRICS and to with job output  filename=${JOB_NAME}_METRICS, same for logs
# 

}


containerdbdemo () 
{

AZCONTAINERNAME=${APPNAME}-$RANDOM


COSMOS_DB_NAME=aci-cosmos-db-$RANDOM
echo "creating databbase for container  $COSMOS_DB_NAME"

COSMOS_DB_ENDPOINT=$(az cosmosdb create \
  --resource-group $RG \
  --name $COSMOS_DB_NAME \
  --query documentEndpoint \
  --output tsv)

COSMOS_DB_MASTERKEY=$(az cosmosdb keys list \
  --resource-group $RG \
  --name $COSMOS_DB_NAME \
  --query primaryMasterKey \
  --output tsv)

echo "creating container $AZCONTAINERNAME"
az container create \
  --resource-group $RG \
  --name $AZCONTAINERNAME \
  --image microsoft/azure-vote-front:cosmosdb \
  --ip-address Public \
  --location $AZLOCATION \
  --secure-environment-variables \
    COSMOS_DB_ENDPOINT=$COSMOS_DB_ENDPOINT \
    COSMOS_DB_MASTERKEY=$COSMOS_DB_MASTERKEY


az container show \
  --resource-group $RG \
  --name $AZCONTAINERNAME \
  --query ipAddress.ip \
  --output tsv
}

### stoping containers
# https://docs.microsoft.com/en-us/azure/container-instances/container-instances-restart-policy


# connecting to azure storage from a container
# 1) use managed identities https://docs.microsoft.com/en-us/azure/container-instances/container-instances-managed-identity

# triggering from azure function
# https://docs.microsoft.com/en-us/azure/container-instances/container-instances-tutorial-azure-function-trigger
