###########
# 
# container, queue and table for jobs
# TODO use the existing storage account for all of this
# so that they can be read by the web application
# then also need to grant permission on that SA for 
# this function app using the system assigned identity

##################
# function app storage
# this storage account is used for code/state etc for functions, not for anything else
resource "azurerm_storage_account" "fnstorage" {
  name                     = "${var.project}${var.env}mlsa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags = "${local.common_tags}"
}


resource "azurerm_storage_container" "jobs" {
  name                  = "jobs"
  storage_account_name  = azurerm_storage_account.fnstorage.name
  container_access_type = "private"
}

resource "azurerm_storage_queue" "jobprocessing" {
  name                 = "jobprocessing"
  storage_account_name = azurerm_storage_account.fnstorage.name
}



###########
# function plan and app

resource "azurerm_service_plan" "ml_runner" {
  name                = "${var.project}-${var.env}-fnplan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            =  var.function_app_sku_name

  tags = "${local.common_tags}"

}

#### function app 
# reference https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_function_app
resource "azurerm_linux_function_app" "ml_runner" {
  name                = local.fn_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name = azurerm_storage_account.fnstorage.name
  storage_account_access_key = azurerm_storage_account.fnstorage.primary_access_key

  service_plan_id      = azurerm_service_plan.ml_runner.id

  site_config {
    application_stack { 
        python_version = "3.8" 
    }
  }

  # list of all app settings : https://docs.microsoft.com/en-us/azure/azure-functions/functions-app-settings
  app_settings  = {
    FUNCTIONS_WORKER_RUNTIME    = "python",
    AZURE_FUNCTIONS_ENVIRONMENT = var.azure_functions_environment,
    PYTHON_ENABLE_DEBUG_LOGGING = var.python_enable_debug_logging,
    ENABLE_ORYX_BUILD           = true,
    SCM_DO_BUILD_DURING_DEPLOYMENT = true,
    
    DATA_PATH = "${var.data_path}"
    JOBS_PATH = "${var.jobs_path}"
    CALLBACK_URL = "${local.web_app_name}.azurewebsites.net/jobs/"

    QUEUECONNECTIONSTRING  = azurerm_storage_account.fnstorage.primary_connection_string
    
    # these are no longer used (blob & table storage)
    # STORAGE_CONTAINER_NAME = azurerm_storage_container.jobs.name #azurerm_storage_queue.jobprocessing.name,
    # STORAGE_TABLE_NAME     = azurerm_storage_table.jobstatus.name,

  }

  tags = "${local.common_tags}"
}


###############
#  mount the file name
# TODO use a local provisioner to run this

#https://docs.microsoft.com/en-us/azure/azure-functions/storage-considerations?tabs=azure-cli#mount-file-shares

# this uses 'heredoc' format for multiline strings.  see terraform doc
output "fn_storage_command" {

  value = <<CMD
  export AZSTORAGE_CUSTOM_ID=$(az webapp identity show --resource-group ${azurerm_resource_group.main.name} \
    --name ${azurerm_linux_function_app.ml_runner.name} --query principalId --output tsv) 

  export AZSTORAGE_KEY=$(az storage account keys list --resource-group ${azurerm_resource_group.main.name} \
    --account-name ${azurerm_storage_account.mldata.name} \
    --query "[0].value" --output tsv)
  
  az webapp config storage-account add -g ${azurerm_resource_group.main.name} \
    -n $ --custom-id anything  \
    --storage-type AzureFiles  \
    --account-name ${azurerm_storage_account.mldata.name} \
    --share-name ${azurerm_storage_share.mldata.name}  \
    --access-key $AZSTORAGE_KEY \
    --mount-path ${var.mount_path}
  CMD

  description="the shell script AZ cli commands to connect GP file storage to function app "

}


output "fn_existing_storage_mount" {

  value = <<CMD
  export AZSTORAGE_CUSTOM_ID=$(az webapp identity show --resource-group ${azurerm_resource_group.main.name} \
    --name ${azurerm_linux_function_app.ml_runner.name} --query principalId --output tsv) 

  export AZSTORAGE_KEY=$(az storage account keys list --resource-group ${var.existing_storage_account_rg} \
    --account-name ${var.existing_storage_account_name} \
    --query "[0].value" --output tsv)
  
  az webapp config storage-account add -g ${azurerm_resource_group.main.name} \
    -n $ --custom-id anything  \
    --storage-type AzureFiles  \
    --account-name ${var.existing_storage_account_name} \
    --share-name ${var.existing_storage_account_share_name}  \
    --access-key $AZSTORAGE_KEY \
    --mount-path ${var.mount_path}
  CMD

  description="the shell script AZ cli commands to connect GP file storage to function app "

}


