terraform {
  required_version = ">=1.1"

  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "~>3.23"
    }
    azapi = {
      source = "azure/azapi"
    }
  }

}

############
# providers
provider "azurerm" {
  features {}
}

provider "azapi" {
}

# for random id used in tags
provider "random"{}

# for timestamp() function used in tags
provider "time"{} 

resource "random_string" "random_id" {
  length  = 6
  numeric  = false
  upper   = false
  special = false
}