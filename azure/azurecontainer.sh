source azure/azuredeploy.sh
# set ACR, etc
az_set_vars

export AZCONTAINERNAME=${IMAGE}_backend
export BACKEND_IMAGE=$AZCONTAINERNAME
export AZBACKENDIMAGE_URL=$ACR.azurecr.io/$BACKEND_IMAGE:$TAG

build_docker_backend ()
{
  az acr build -t $BACKEND_IMAGE:$TAG -r $ACR .
}

test_create_container ()
{

# DNS_NAME_LABEL=${APPNAME}-$RANDOM
# echo "using $DNS_NAME_LABEL"

CONTAINER_ENV_VARS=`paste -sd " " azure/dockerenv`
az container create \
  --resource-group $RG \
  --name $AZCONTAINERNAME \
  --image $AZBACKENDIMAGE_URL \
  --location $AZLOCATION
  --os-type Linux
  --restart-policy Never
  --environment-variables $CONTAINER_ENV_VARS

  # --azure-file-volume-account-key
  # --azure-file-volume-account-name
  # --azure-file-volume-mount-path
  # --azure-file-volume-share-name
#   --dns-name-label $DNS_NAME_LABEL \

echo "container status"
az container show \
  --resource-group $RG \
  --name $AZCONTAINERNAME \
  --query containers[0].instanceView.currentState.state

az container logs \
  --resource-group $RG \
  --name $AZCONTAINERNAME

# I'm guessing on this one
az container delete \
  --resource-group $RG \
  --name $AZCONTAINERNAME \

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
