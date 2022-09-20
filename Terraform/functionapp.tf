###########
# 
# container, queue and table for jobs
# TODO use the existing storage account for all of this
# so that they can be read by the web application
# then also need to grant permission on that SA for 
# this function app using the system assigned identity


resource "azurerm_log_analytics_workspace" "appInsight" {
  name                = "workspace-${var.project}-${var.env}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "appInsight" {
  name                = "insights-${var.project}-${var.env}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "other"
}


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
  maximum_elastic_worker_count = var.function_maximum_elastic_worker_count
  tags = "${local.common_tags}"

}

#### function app 
# reference https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_function_app
resource "azurerm_linux_function_app" "ml_runner" {
  name                = local.fn_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name = azurerm_storage_account.fnstorage.name
  storage_uses_managed_identity = true
  # key is not needed if using managed identity, but kept here for reference 
  # during dev as we are trying both methods
  # storage_account_access_key = azurerm_storage_account.fnstorage.primary_access_key

  service_plan_id      = azurerm_service_plan.ml_runner.id

  site_config {
    application_stack { 
        python_version = "3.8" 
    }
  }

  identity {
      type = "SystemAssigned"
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
    CALLBACK_URL = "https://${local.web_app_name}.azurewebsites.net/jobs/"
    QUEUECONNECTIONSTRING  = azurerm_storage_account.fnstorage.primary_connection_string
  
    AzureWebJobsStorage__accountName = azurerm_storage_account.fnstorage.name
    
    APPINSIGHTS_INSTRUMENTATIONKEY = "${azurerm_application_insights.appInsight.instrumentation_key}"
  
  }

  tags = "${local.common_tags}"

  provisioner "local-exec" {
    command= <<CMD

    CMD
  }
}

# # allow function app access to shared ML data storage
# # note this is not for access to the storage acccount used to run the function 
# resource "azurerm_role_assignment" "ml_runner_ml_storage" {
#   principal_id = azurerm_linux_function_app.ml_runner.identity[0].principal_id
#   role_definition_name = "Storage File Data SMB Share Contributor"
#   scope = azurerm_resource_group.main.id  

#   # scope = azurerm_storage_account.mldata.id 
# }


# resource "azurerm_role_assignment" "existing_ml_storage" {
#   principal_id = azurerm_linux_function_app.ml_runner.identity[0].principal_id
#   role_definition_name = "Storage File Data SMB Share Contributor"
#   scope = data.azurerm_subscription.main.id
#   # scope = azurerm_storage_account.mldata.id 
# }

# give function access to storage for running
# this is all using the portal https://docs.microsoft.com/en-us/samples/azure-samples/functions-storage-managed-identity/using-managed-identity-between-azure-functions-and-azure-storage/
# list of roles needed https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference?tabs=blob#connecting-to-host-storage-with-an-identity-preview

resource "azurerm_role_assignment" "ml_runner_function_storage" {
  principal_id = azurerm_linux_function_app.ml_runner.identity[0].principal_id
  role_definition_name = "Storage Account Contributor"
  # "Storage Blob Data Owner"
  # Storage Account Contributor,
  # Storage Blob Data Owner,
  # Storage Queue Data Contributor

  scope = azurerm_resource_group.main.id  

  # scope = azurerm_storage_account.fnstorage.id 
}



###############
# connect function storage share used to hold ML back-end data and Jobs 
# web app resources have a means to mount file shares with SMB.   Functions don't fully document this but it's possible
# terraform does not support it but we can make it happen with the Azure CLI. 
# 
#https://docs.microsoft.com/en-us/azure/azure-functions/storage-considerations?tabs=azure-cli#mount-file-shares


resource "null_resource" "mount_mldata_storage_to_fnapp" {
  # shell script to mount the additional file share with ML input/output to the function app.  

  # since the resources in use are inside the command, have to call them out here so they are completed
  # prior to running this script
  depends_on = [azurerm_linux_function_app.ml_runner,azurerm_storage_account.mldata]
  
  # if the function ID changes, we can assume that we have to re-run the storage adding command
  triggers = {
    function_id = azurerm_linux_function_app.ml_runner.identity[0].principal_id
  }
  
  # Azure CLI shell script, tested on MacOS/Bash
  provisioner "local-exec" {
    command= <<CMD
  AZSTORAGE_CUSTOM_ID=$(az webapp identity show --resource-group ${azurerm_resource_group.main.name} \
    --name ${azurerm_linux_function_app.ml_runner.name} --query principalId --output tsv) 

  AZSTORAGE_KEY=$(az storage account keys list --resource-group ${azurerm_resource_group.main.name} \
    --account-name ${azurerm_storage_account.mldata.name} \
    --query "[0].value" --output tsv)
  
  az webapp config storage-account add -g ${azurerm_resource_group.main.name} \
    -n ${azurerm_linux_function_app.ml_runner.name} --custom-id $AZSTORAGE_CUSTOM_ID \
    --storage-type AzureFiles  \
    --account-name ${azurerm_storage_account.mldata.name} \
    --share-name ${azurerm_storage_share.mldata.name}  \
    --access-key $AZSTORAGE_KEY \
    --mount-path ${var.mount_path}
    CMD
  }

}


# output "fn_existing_storage_mount" {

#   value = <<CMD
#   export AZSTORAGE_CUSTOM_ID=$(az webapp identity show --resource-group ${azurerm_resource_group.main.name} \
#     --name ${azurerm_linux_function_app.ml_runner.name} --query principalId --output tsv) 

#   export AZSTORAGE_KEY=$(az storage account keys list --resource-group ${var.existing_storage_account_rg} \
#     --account-name ${var.existing_storage_account_name} \
#     --query "[0].value" --output tsv)
  
#   az webapp config storage-account add -g ${azurerm_resource_group.main.name} \
#     -n $ --custom-id anything  \
#     --storage-type AzureFiles  \
#     --account-name ${var.existing_storage_account_name} \
#     --share-name ${var.existing_storage_account_share_name}  \
#     --access-key $AZSTORAGE_KEY \
#     --mount-path ${var.mount_path}
#   CMD

#   description="the shell script AZ cli commands to connect GP file storage to function app "

# }


