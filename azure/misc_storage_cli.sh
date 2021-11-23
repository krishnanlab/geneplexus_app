# MISC cli code for working with azure storage
# check that these are in azuredeploy.sh

export AZSTORAGEKEY=$(az storage account keys list \
    --resource-group $AZRG \
    --account-name $AZSTORAGENAME \
    --query "[0].value" | tr -d '"')

az storage share exists \
    --account-key $AZSTORAGEKEY \
    --account-name $AZSTORAGENAME --name $AZSHARENAME


# https://docs.microsoft.com/en-us/azure/storage/files/storage-how-to-use-files-cli

az storage share create \
    --account-name $AZSTORAGENAME \
    --account-key $AZSTORAGEKEY \
    --name $AZSHARENAME \
    --quota 1024 \
    --enabled-protocols SMB

# BUT https://docs.microsoft.com/en-us/cli/azure/storage/share?view=azure-cli-latest#az_storage_share_create
