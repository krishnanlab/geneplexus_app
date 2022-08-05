###########
# 
# container, queue and table for jobs
# TODO use the existing storage account for all of this
# so that they can be read by the web application
# then also need to grant permission on that SA for 
# this function app using the system assigned identity

resource "azurerm_storage_container" "jobs" {
  name                  = "jobs"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_queue" "jobprocessing" {
  name                 = "jobprocessing"
  storage_account_name = azurerm_storage_account.main.name
}

resource "azurerm_storage_table" "jobstatus" {
  name                 = "jobstatus"
  storage_account_name = azurerm_storage_account.main.name
}


###########
# function plan and app

resource "azurerm_service_plan" "ml_runner" {
  name                = "${var.project}-${var.env}-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            =  var.function_app_sku_name

  tags = "${local.common_tags}"

}

#### function app 
# reference https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_function_app
resource "azurerm_linux_function_app" "ml_runner" {
  name                = "${var.project}-${var.env}-fn"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

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
    
    DATA_PATH = "${var.mount_path}/data"
    JOBS_PATH = "${var.jobs_path}/jobs"
    
    STORAGE_CONTAINER_NAME = azurerm_storage_container.jobs.name #azurerm_storage_queue.jobprocessing.name,
    STORAGE_TABLE_NAME     = azurerm_storage_table.jobstatus.name,
    QUEUECONNECTIONSTRING  = azurerm_storage_account.main.primary_connection_string

  }

  tags = "${local.common_tags}"
}


output "fn_storage_command" {
  value = <<EOT
  az webapp config storage-account add -g ${azurerm_resource_group.main.name} \
    -n $ --custom-id anything  \
    --storage-type AzureFiles  \
    --account-name ${azurerm_storage_account.mldata.name} \
    --share-name ${azurerm_storage_share.mldata.name}  \
    --access-key ${azurerm_storage_account.mldata.primary_access_key} \
    --mount-path ${var.mount_path}
  EOT
}
