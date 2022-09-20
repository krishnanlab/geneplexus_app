

######  database
# from https://gmusumeci.medium.com/how-to-deploy-an-azure-database-for-postgresql-using-terraform-a35a0e0ded68
resource "azurerm_postgresql_server" "gpapp-db" {
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

### Firewall rules for application database
# this opens the db to any other Azure server
# this is for development only while testing more restrictive rules, and should be removed for production
resource "azurerm_postgresql_firewall_rule" "all-azure" {
  name                = "azure_all_services"
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.gpapp-db.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
}

### Firewall rules for application database
# goal: only allow access to the database from the flask web app.  The fn app does not need access
# this block uses the list of main IP addresses from the web app and the 'count' feature to create rule for each

# TODO THIS DOESN'T WORK
# terraform won't use 'count' that depends on resources to be created
# solution is to use 'target' but that is discouraged
# see https://stackoverflow.com/questions/64971807/mysql-firewall-rules-from-an-app-services-outbound-ips-on-azure-using-terraform
# for complex solution and run TF twice.   
# the OTHER solution is to run a provisioner local exec, and use AZ CLI to create this rules
# with a basic for-loop in bash/etc
# resource "azurerm_postgresql_firewall_rule" "gpapp-db" {
#   resource_group_name = azurerm_resource_group.main.name
#   server_name         = azurerm_postgresql_server.gpapp-db.name
#   count               = length(azurerm_linux_web_app.gpapp.outbound_ip_address_list) 
#   name                = "app_service_${count.index}"
#   start_ip_address    = azurerm_linux_web_app.gpapp.outbound_ip_address_list[count.index]
#   end_ip_address      = azurerm_linux_web_app.gpapp.outbound_ip_address_list[count.index]
# }

### Application Database
# the database instance to 
resource "azurerm_postgresql_database" "postgresql-db" {
  name                = var.database-instance-name
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.gpapp-db.name
  charset             = "utf8"
  collation           = "English_United States.1252"
}

### Database connection string
# for use outside of the web app
# the web app is configured by terraform to use this connection string
# note requires that the firewall is open to whereever you connect from (cloud shell or laptop)
output "psql_command"{
  sensitive = true
	value = "host=${azurerm_postgresql_server.gpapp-db.name}.postgres.database.azure.com port=5432 dbname=${azurerm_postgresql_database.postgresql-db.name} user=${azurerm_postgresql_server.gpapp-db.administrator_login}@${azurerm_postgresql_server.gpapp-db.name} sslmode=require"
}
