############ variables.tf
##### geneplexus app

# existing resources
variable "existing_storage_account_rg" {
  type = string
  default = ""
}

variable "existing_storage_account_name" {
  type = string
  default = ""
}

variable "existing_storage_account_share_name" {
  type = string
  default = ""
}


#####
# project level variables (used to name and tag things)

variable "project" {
  description = "Name of project, used in naming resources and tags"
  type = string
  default = "geneplexusml"
}

variable "env" {
  description = "working environment (dev, prod, test, training)"
  type = string
  default = "dev"
}

variable "location" {
  description = "Azure location name"
  type = string
  default = "Central US"
}

variable "userid" {
  description = "Id of user for use in tagging resources"
  type = string
  default = ""
}

###########
# database

variable "postgresql-admin-login" {
  type = string
  description = "user ID for the main admin login for project db"
  default = ""
}

variable "postgresql-admin-password" {
type = string
  description = "pw for server admin (not db).  replace with keyvault eventually"
}

variable "postgresql-version" {
  type = string
  description = "the version of postgres to use"
  default = "11"
}

variable "postgresql-sku-name" {
  type = string
  description = "basic tier"
  default = "B_Gen5_1"
}

variable "postgresql-storage-mb" {
  #TODO consider using an int instead of string
  type = string
  description = "total storage request for the start of the db"
  default = "5120"
}

variable "database-instance-name" {
  type = string
  description = "name of the database, not the server, required"
}

# this is a developmen setting, to allow db access outside of the app
# you can also set access to all azure services, and access from cloud shell during dev
# the FW rules should allow access from the the web app for create-db command
# variable "ipaddress-db-access" {
#   type = string
#   description = "ip address to acces db for psql"
#   default = "0.0.0.0"

# }



############
# azure functions configuration options

variable "azure_functions_environment" {
  type = string
  description = "Development, Staging, or Production "
  default = "Development"

}

variable "python_enable_debug_logging" {
  type = number
  description = "1 to turn on debug, 0 off. set to 0 for production environments. default 1"
  default = 1

}

variable "function_app_sku_name" {
  type = string
  description = "Function SKU for Elastic or Consumption function app plans (Y1, EP1, EP2, and EP3)"
  # Geneplexus needs at least 7gb to run and perhaps more
  default =  "EP3"
}

variable "function_maximum_elastic_worker_count" {
  type = number
  description = "Function app maximum workers allowed to scale to for Elastic or Consumption function app plans"
  default =  10
}

variable "mount_path" {
  type = string
  description = "the base path where jobs are stored"
  default =  "/geneplexus_files"
}

variable "data_path" {
  type = string
  description = "the path where data folder is mounted in function app"
  default =  "/geneplexus_files/geneplexus_data"
}

variable "jobs_path" {
  type = string
  description = "the based path where jobs are stored"
  default =  "/geneplexus_files/jobs"
}

variable "github_id_for_auth" {
  type = string
  description = "id from github after registering this app, default is empty string so app can be created before registering"
  default =  ""
}

variable "github_secret_for_auth" {
  type = string
  description = "secret from github after registering this app, default is empty string so app can be created before registering"
  default =  ""
}


########## 
#computed variables (locals)

locals {
  # Common tags to be assigned to all resources
  # id number can be used to select and delete resources
  common_tags = {
    created_by = var.userid
    project   = var.project
    environment = var.env
    id = random_string.random_id.result
  }

  # calculate these here so they can be used without circular reference ('cycle' in TF terms)
  web_app_name = "${var.project}-${var.env}"
  fn_app_name  = "${var.project}-${var.env}-fn"

}

