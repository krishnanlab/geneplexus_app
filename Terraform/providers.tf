terraform {
  required_version = ">=1.1"

  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "~>3.7"
    }
  }

}

############
# providers
provider "azurerm" {
  features {}
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