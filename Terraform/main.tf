######## main.tf
##### geneplexus app project: web app, database and function app terraform 

# this creates resources to run the PythonGeneplexus package as an azure function
# see the readme.md in the folder above for details


############
# existing resources to tie in 

    # data "azurerm_storage_account" "geneplexus_storage" {
    #   # https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/storage_account
    #   name                = var.existing_storage_account_name
    #   resource_group_name = var.existing_storage_account_rg
    # }

# azurerm_storage_account.geneplexus_storage.primary_access_key , primary_file_endpoint 

############
# resources

resource "azurerm_resource_group" "main" {
  name     = "${var.project}-${var.env}-rg"
  location = var.location

  tags = "${local.common_tags}"
}

output "AZRG" {
  value = azurerm_resource_group.main.name
  description = "resource group"
}



output "function_app_id" {
  value = azurerm_linux_function_app.ml_runner.id
  description = "function app id"
}

output "AZFN" {
  value = azurerm_linux_function_app.ml_runner.name
  description = "function app name"
}

output "function_app_default_hostname" {
  value = azurerm_linux_function_app.ml_runner.default_hostname
  description = "function app hostname"
}
