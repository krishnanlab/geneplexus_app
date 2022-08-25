

######  database
# from https://gmusumeci.medium.com/how-to-deploy-an-azure-database-for-postgresql-using-terraform-a35a0e0ded68
resource "azurerm_postgresql_server" "postgresql-server" {
  name                         = "${var.project}-${var.env}-pgserver"
  location                     = azurerm_resource_group.main.location
  resource_group_name          = azurerm_resource_group.main.name
 
  administrator_login          = var.postgresql-admin-login
  administrator_login_password = var.postgresql-admin-password
 
  sku_name = var.postgresql-sku-name
  version  = var.postgresql-version
 
  storage_mb        = var.postgresql-storage-mb
  auto_grow_enabled = true
  
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  public_network_access_enabled     = true
  ssl_enforcement_enabled           = true
  ssl_minimal_tls_version_enforced  = "TLS1_2"
  tags = local.common_tags
}

resource "azurerm_postgresql_database" "postgresql-db" {
  name                = var.database-instance-name
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.postgresql-server.name
  charset             = "utf8"
  collation           = "English_United States.1252"
}

output "psql_command"{
	value = "host=${azurerm_postgresql_server.postgresql-server.name}.postgres.database.azure.com port=5432 dbname=${azurerm_postgresql_database.postgresql-db.name} user=${azurerm_postgresql_server.postgresql-server.administrator_login}@${azurerm_postgresql_server.postgresql-server.name} sslmode=require"
}
