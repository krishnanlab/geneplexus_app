# storage.tf
# storage for this system is needed for 
# 1) file shares in an account for backend data, read is all that's needed
# 2) file share for job storage, read/write (with future coding be blob storage)
# 3) functionapp storage account; shares etc are created automatically as needed.  
#  notes 
#     there seems to be just one file mount possible for functions, so 1 and 2 must be in same share
#     the storage account for function operation is created with the function functionapp.tf




##################
# existing storage
#
# the system depends on a large body of 'backend' data currently available on zenodo
# this terraform does not have scripts to download to a storage account from zenodo 
# so it currently assumes that there is an existing storage account used only for 
# keeping these data on azure in a place that the different environments created 
# with terraform can copy. 
#  
data "azurerm_storage_account" "existing_storage_account" {
  name                = var.existing_storage_account_name
  resource_group_name = var.existing_storage_account_rg

}

data "azurerm_storage_share" "existing_storage_account_share" {
  name                 = var.existing_storage_account_share_name
  storage_account_name = var.existing_storage_account_name
}

data "azurerm_storage_account_sas" "existing_storage_account" {
  connection_string = data.azurerm_storage_account.existing_storage_account.primary_connection_string
  https_only        = true

  resource_types {
    service   = true
    container = true
    object    = true
  }

  services {
    blob  = false
    queue = false
    table = false
    file  = true
  }

  start  = "2022-01-01T00:00:00Z"
  expiry = "2022-12-31T00:00:00Z"

  permissions {
    read    = true
    write   = false
    delete  = false
    list    = true
    add     = false
    create  = false
    update  = false
    process = false
    tag     = false
    filter  = false
  }
}


#################
# NEW ML data and job storage for file shares mounted on apps
# new storage account for storing job and backend data, must have file shares 
resource "azurerm_storage_account" "mldata" {
  name                     = "${var.project}${var.env}storage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Premium"
  account_replication_type = "LRS"
  shared_access_key_enabled  = true
  account_kind             = "FileStorage"
  tags                     = local.common_tags
}

### this turns on 'AzureFiles' in the storage account above, for mounting in 
# both this web app and the function app 
resource "azurerm_storage_share" "mldata" {
  name                 = "${var.project}${var.env}files"
  storage_account_name = azurerm_storage_account.mldata.name
  quota                = 100
  enabled_protocol     = "SMB"

}


#### SAS for access to copy into new storage
data "azurerm_storage_account_sas" "mldata" {
  connection_string = azurerm_storage_account.mldata.primary_connection_string
  https_only        = true

  resource_types {
    service   = true
    container = true
    object    = true
  }

  services {
    blob  = false
    queue = false
    table = false
    file  = true
  }

  start  = "2022-01-01T00:00:00Z"
  expiry = "2022-12-31T00:00:00Z"

  permissions {
    read    = true
    write   = true
    delete  = false
    list    = true
    add     = true
    create  = true
    update  = true
    process = false
    tag     = false
    filter  = false
  }
}


##############
# COPY the data from the existing storage account
# azcopy copy '<local-directory-path>/*' 'https://<storage-account-name>.file.core.windows.net/<file-share-name>/<directory-path><SAS-token>'
# assume source data is in folder "geneplexus_data" and app-mounted storage also uses geneplexus_data for back-end data

# resource "null_resource" "copy_mldata" {

#   depends_on = [data.azurerm_storage_account.existing_storage_account,
#                 data.azurerm_storage_share.existing_storage_account_share,
#                 azurerm_storage_account.mldata,
#                 azurerm_storage_share.mldata,
#                 data.azurerm_storage_account_sas.mldata,
#                 data.azurerm_storage_account_sas.existing_storage_account
#   ]

#   triggers = { "SASstrings" = "${data.azurerm_storage_account_sas.mldata.sas} ${data.azurerm_storage_account_sas.existing_storage_account.sas}"}
  
#   provisioner "local-exec" {
#         command= <<CMD
#      azcopy copy \
#     'https://${data.azurerm_storage_account.existing_storage_account.name}.file.core.windows.net/${data.azurerm_storage_share.existing_storage_account_share.name}/geneplexus_data${data.azurerm_storage_account_sas.existing_storage_account.sas}' \
#     'https://${azurerm_storage_account.mldata.name}.file.core.windows.net/${azurerm_storage_share.mldata.name}/geneplexus_data${data.azurerm_storage_account_sas.mldata.sas}' --recursive
#         CMD
#     }
# }

#########
# create job folder
# the storage share has a folder for storing job outputs

# az storage directory create --name jobs \
#                           --share-name geneplexusmldevfiles \
#                            --account-name  geneplexusmldevstorage \
#                            --sas-token $dest_sas

resource "null_resource" "create_job_folder" {
    provisioner "local-exec" {
        command= <<CMD
az storage directory create --name "jobs" \
--account-name ${azurerm_storage_account.mldata.name} \
--share-name ${azurerm_storage_share.mldata.name} \
--sas-token ${data.azurerm_storage_account_sas.mldata.sas}
        CMD
    }
}

resource "null_resource" "create_data_folder" {
  
    depends_on = [data.azurerm_storage_account.existing_storage_account, 
      data.azurerm_storage_account_sas.existing_storage_account,
      azurerm_storage_account.mldata,
      data.azurerm_storage_account_sas.mldata
    ]

    provisioner "local-exec" {
        command= <<CMD
az storage directory create --name "geneplexus_data" \
--account-name ${azurerm_storage_account.mldata.name} \
--share-name ${azurerm_storage_share.mldata.name} \
--sas-token ${data.azurerm_storage_account_sas.mldata.sas}

azcopy copy \
'https://${data.azurerm_storage_account.existing_storage_account.name}.file.core.windows.net/${data.azurerm_storage_share.existing_storage_account_share.name}/geneplexus_data${data.azurerm_storage_account_sas.existing_storage_account.sas}' \
'https://${azurerm_storage_account.mldata.name}.file.core.windows.net/${azurerm_storage_share.mldata.name}${data.azurerm_storage_account_sas.mldata.sas}' --recursive

        CMD
    }
}

output "cmd_to_copy_files" {
  value = <<CMD
azcopy copy \
'https://${data.azurerm_storage_account.existing_storage_account.name}.file.core.windows.net/${data.azurerm_storage_share.existing_storage_account_share.name}/geneplexus_data${data.azurerm_storage_account_sas.existing_storage_account.sas}' \
'https://${azurerm_storage_account.mldata.name}.file.core.windows.net/${azurerm_storage_share.mldata.name}${data.azurerm_storage_account_sas.mldata.sas}' --recursive
            CMD

  sensitive = true
  description = "azcopy command to copy data backend from known azure file location to file share for this environment"
}

# output "cmd_to_make_jobs_folder" {
#   value =  <<CMD
# az storage directory create --name "jobs" \
# --account-name ${azurerm_storage_account.mldata.name} \
# --share-name ${azurerm_storage_share.mldata.name} \
# --sas-token ${data.azurerm_storage_account_sas.mldata.sas}
#         CMD
    
#   description = "run this if the provisioner doesn't work"
#   sensitive = true
# }


output "AZSA" {
  value = azurerm_storage_account.mldata.name
  description = "storage account name used for machine learning"
}

output "AZSHARE" {
  value = azurerm_storage_share.mldata.name
  description = "name of storage share"
}

# this code is currently living in functionapp.tf

# # this uses 'heredoc' format for multiline strings.  see terraform doc
# output "fn_storage_command" {

#   value = <<CMD
#   export AZSTORAGE_CUSTOM_ID=$(az webapp identity show --resource-group ${azurerm_resource_group.main.name} \
#     --name ${azurerm_linux_function_app.ml_runner.name} --query principalId --output tsv) 

#   export AZSTORAGE_KEY=$(az storage account keys list --resource-group ${azurerm_resource_group.main.name} \
#     --account-name ${azurerm_storage_account.mldata.name} \
#     --query "[0].value" --output tsv)
  
#   az webapp config storage-account add -g ${azurerm_resource_group.main.name} \
#     -n $ --custom-id anything  \
#     --storage-type AzureFiles  \
#     --account-name ${azurerm_storage_account.mldata.name} \
#     --share-name ${azurerm_storage_share.mldata.name}  \
#     --access-key $AZSTORAGE_KEY \
#     --mount-path ${var.mount_path}
#   CMD

#   description="the shell script AZ cli commands to connect GP file storage to function app "

# }


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



