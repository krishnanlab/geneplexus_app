######## webapp.tf
##### geneplexus app project: web app terraform 


###
# reference https://docs.microsoft.com/en-us/azure/app-service/configure-connect-to-azure-storage?tabs=portal&pivots=container-linux
# "Mounting the storage to /home is not recommended because it may result in performance bottlenecks for the app.""

variable "mount_path"{
  type = string
  description = "the base path where jobs are stored"
  default =  "/geneplexus_files"
}

# storage account for storing job and backend data, must have file shares 


resource "azurerm_storage_account" "mldata" {
  name                     = "${var.project}${var.env}storage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Premium"
  account_replication_type = "LRS"
  shared_access_key_enabled  = true
  tags                     = local.common_tags
}

### this turns on 'AzureFiles' in the storage account above, for mounting in 
# both this web app and the function app 
resource "azurerm_storage_share" "mldata" {
  name                 = "${var.project}${var.env}files"
  storage_account_name = azurerm_storage_account.mldata.name
  quota                = 50
  enabled_protocol     = "SMB"
}


resource "azurerm_service_plan" "gpapp" {
  name                = "${var.project}-${var.env}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "P1v2"
  tags                = local.common_tags
}


# reference https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_web_app
resource "azurerm_linux_web_app" "gpapp" {
  name                = "${var.project}-${var.env}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.gpapp.id
  tags                = local.common_tags

  site_config {
    app_command_line = "" #  (Optional) The App command line to launch.
    application_stack {
        python_version = "3.8" 
        } 
    ftps_state = "Disabled" # - (Optional) The State of FTP / FTPS service. Possible values include: AllAllowed, FtpsOnly, Disabled.
    }

  logs {
    application_logs {
     file_system_level = "Information" 
    }
  }

  storage_account {
       # this connects the storage account with the web application
        access_key = azurerm_storage_account.mldata.primary_access_key
        account_name =  azurerm_storage_account.mldata.name  # (Required) The Name of the Storage Account.
        name = azurerm_storage_share.mldata.name # - ??? (Required) The name which should be used for this Storage Account, no spaces
        share_name = azurerm_storage_share.mldata.name   # - (Required) The Name of the File Share or Container Name for Blob storage.
        type = "AzureFiles" # - (Required) The Azure Storage Type. Possible values include AzureFiles and AzureBlob
        mount_path = var.mount_path 
    }

  identity {
        type = "SystemAssigned"
    }

  app_settings = {
    "DATA_PATH"="${var.mount_path}/data"
    "JOB_PATH"= "${var.mount_path}/jobs"
    "QUEUE_URL"="${azurerm_linux_function_app.ml_runner.default_hostname}/api/enqueue"
    "SQLALCHEMY_DATABASE_URI"="sqlite:///test.db"
  }

}

output "giturl" { 
  value= "https://username@${azurerm_linux_web_app.gpapp.name}.scm.azurewebsites.net/${azurerm_linux_web_app.gpapp.name}.git"
  description = "remote git url for web app"

}

output "git-config-command" {
  value = "az webapp deployment source config-local-git --name ${azurerm_linux_web_app.gpapp.name} --resource-group ${azurerm_resource_group.main.name}"
  description = " this is the command to run to set up local git deployment"
}