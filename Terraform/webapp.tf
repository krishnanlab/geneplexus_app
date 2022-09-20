######## webapp.tf
##### geneplexus app project: web app terraform 


###
# reference https://docs.microsoft.com/en-us/azure/app-service/configure-connect-to-azure-storage?tabs=portal&pivots=container-linux
# "Mounting the storage to /home is not recommended because it may result in performance bottlenecks for the app.""


resource "azurerm_service_plan" "gpapp" {
  name                = "${var.project}-${var.env}-appplan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "P1v2"
  tags                = local.common_tags
}


# reference https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_web_app
resource "azurerm_linux_web_app" "gpapp" {

  depends_on = [
    azurerm_storage_account.mldata
  ]

  name                = local.web_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.gpapp.id
  tags                = local.common_tags

  site_config {
    application_stack {
        python_version = "3.8" 
        } 
    # ftps_state = "Disabled" # - (Optional) The State of FTP / FTPS service. Possible values include: AllAllowed, FtpsOnly, Disabled.
    }

  logs {
    application_logs {
     file_system_level = "Information" 
    }
  }
  
  storage_account {
       # this connects the storage account with the web application
       # note that permissions are still required, see role granting below
        access_key = azurerm_storage_account.mldata.primary_access_key
        account_name =  azurerm_storage_account.mldata.name 
        name = "${azurerm_storage_share.mldata.name}share" # - ??? (Required) The name which should be used for this share
        share_name = azurerm_storage_share.mldata.name   
        type = "AzureFiles" 
        mount_path = var.mount_path 
    }

  identity {
        type = "SystemAssigned"
    }

# note for DATABASE URI ssl mode options, see https://www.postgresql.org/docs/current/libpq-ssl.html
# using 'require' does not insist on client side certificate but will encrypt

  app_settings = {
    "DATA_PATH" = "${var.data_path}"
    "JOB_PATH" = "${var.jobs_path}"
    "BASE_URL"  = "https://${local.web_app_name}.azurewebsites.net/"
    "SQLALCHEMY_DATABASE_URI"="postgresql://${azurerm_postgresql_server.gpapp-db.administrator_login}%40${azurerm_postgresql_server.gpapp-db.name}:${var.postgresql-admin-password}@${azurerm_postgresql_server.gpapp-db.name}.postgres.database.azure.com:5432/${azurerm_postgresql_database.postgresql-db.name}?sslmode=require"  
    "LOG_FILE"="/home/site/flask.log"
    "QUEUE_URL"="https://${local.fn_app_name}.azurewebsites.net/api/enqueue"
    "OAUTHLIB_RELAX_TOKEN_SCOPE"="1"
    "GITHUB_ID"="${var.github_id_for_auth}"
    "GITHUB_SECRET"="${var.github_secret_for_auth}"

  }

}

# required RBAC for the web app to be able to access the mounted storage

resource "azurerm_role_assignment" "gpapp_storage_access" {
  # note a bug was reported about getting this index 
  principal_id = azurerm_linux_web_app.gpapp.identity[0].principal_id
  role_definition_name = "Storage File Data SMB Share Contributor"
  scope = azurerm_storage_account.mldata.id
  # alternatively grant for any storage in the whole resource group.  not sure if will work if we use just the storage account
  # assumes the storage account is in the same resource group though! 
  #scope = azurerm_resource_group.main.id  

}

output "giturl" { 
  value= "https://${var.userid}@${azurerm_linux_web_app.gpapp.name}.scm.azurewebsites.net/${azurerm_linux_web_app.gpapp.name}.git"
  description = "remote git url for web app, requires the git userid to be setup for azure web app local git push"

}

output "git-config-command" {
  value = "az webapp deployment source config-local-git --name ${azurerm_linux_web_app.gpapp.name} --resource-group ${azurerm_resource_group.main.name}"
  description = " this is the command to run to set up local git deployment"
}