#! /bin/bash 
# file_share.sh  
# this is a temporary script to learn how the CLI can be used to add file share
# to a function app.  This is necessary to connect the geneplexus data and job files
# so the function app can read/write them.   The goal is to move this into the terraform 
# provisioning script 


# names are from the output of terraform
# the resource group and name of your function. 
export AZFNRG=$(terraform output -raw AZRG)
# AZFNRG=$(terraform output -raw AZRG)
export AZFN=$(terraform output -raw AZFN)

# existing storage
export AZSTORAGE_KEY=$(az storage account keys list --resource-group $AZRG --account-name $AZSTORAGENAME --query "[0].value" --output tsv)
# this function is defined in azuredeploy.sh
export AZSTORAGE_CUSTOM_ID=$(az_get_app_identity) 


az webapp config storage-account add -g $AZFNRG -n $AZFN \
--custom-id $AZSTORAGE_CUSTOM_ID \
--storage-type AzureFiles \
--account-name $AZSTORAGENAME \
--share-name $AZSHARENAME \
--access-key $AZSTORAGE_KEY \
--mount-path /geneplexus_files

# permissions? 

# check it
az webapp config storage-account list --resource-group $AZFNRG --name $AZFN