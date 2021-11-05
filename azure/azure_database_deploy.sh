#############
# APP DATABASE CREATION
# Geneplexus doesn't currently use SQL backend, this code preserved for future features

source azuredeploy.sh

az_app_database_create () 
{

    # Create a PostgreSQL server with a single database instance
    # for this project in the same Resource Group
    # uses  variables defined above eg resource group $AZRG 
    # Name of a server maps to DNS name and is thus required to be globally unique in Azure.
    # Substitute the <server_admin_password> with your own value.


    # PARAMETERS
    AZDBSERVERNAME=${PROJECT}-psql
    DB_NAME=$AZAPPNAME-dev
    DB_ADMIN_NAME=${PROJECT}admin
    # set the server SKU if it is not set already 
    AZDBSKU="${AZDBSKU:-B_GEN5_1}"  # default to small database, basic gen5 1 CPUS  --sku_name
    DBSTORAGE=$((5120+(5*1024)))   # in megabytes --storage_size. min is 5120 10gb => 10250

    # docs for SKU and storage for postgresql on azure
    # https://docs.microsoft.com/en-us/azure/postgresql/quickstart-create-server-database-azure-cli#create-an-azure-database-for-postgresql-server

    # TODO check if db server exists first 
    # TODO check if db exists on that server, requires firewall access to that db from current pc

    echo "creates project database server called $SERVER_NAME in group $AZRG with admin ID $DB_ADMIN_NAME"
    read -p "Enter new password for $DB_ADMIN_NAME (no quote marks please) or ctrl+c to cancel...  " DB_ADMIN_PW

    if [[ -z "$DB_ADMIN_PW" ]]; then
        "No password entered, exiting"
        return 1
    else  
        read -p "confirm password" DB_ADMIN_PW_CONFIRM
        if [[ "$DB_ADMIN_PW" != "$DB_ADMIN_PW_CONFIRM" ]]; then
            echo "passwords don't match, exiting, sorry"    
            return 1
        fi
    fi

    #TODO add tag created_by=$AZUSER

    az postgres server create \
    --name  $AZDBSERVERNAME \
    --resource-group $AZRG \
    --location $AZLOCATION \
    --admin-user $DB_ADMIN_NAME \
    --admin-password $DB_ADMIN_PW \
    --sku-name $AZDBSKU \
    --storage-size $DBSTORAGE \
    --auto-grow Enabled


    # Configure a firewall rule for the server

    echo "opening firewall to MSU wired connections"
    az postgres server firewall-rule create \
    --resource-group $AZRG \
    --server $AZDBSERVERNAME \
    --name allow_msu_wired_358 \
    --start-ip-address 35.10.0.0 \
    --end-ip-address 35.10.255.255

    read -p "Enter your IP to open or blank to skip... " IP_FOR_ACCESS

    if [[ -z "$IP_FOR_ACCESS" ]]; then
        "No IP entered"

    else  
    az postgres server firewall-rule create \
    --resource-group $AZRG \
    --server $AZDBSERVERNAME \
    --name first_allowed_single_IP \
    --start-ip-address $IP_FOR_ACCESS \
    --end-ip-address $IP_FOR_ACCESS

    echo "opened up $SERVER_NAME for $IP_FOR_ACCESS"
    fi

    echo creating $DB_NAME on $AZDBSERVERNAME
    az postgres db create \
        --name $DB_NAME \
        --resource-group $AZRG \
        --server $AZDBSERVERNAME \

    echo "If there were no errors, the database was created.  "
    echo "a psql connection command is (without the password)"
    echo "psql -h $SERVER_NAME.postgres.database.azure.com -U ${DB_ADMIN_NAME}@$SERVER_NAME  $DB_NAME"

    # todo check if azure app service is created, then can set the connection string
    # when that check is in, can add the connection string setting here...
    # az_app_set_dburi

    }

az_app_set_dburi ()
{
    echo "setting the app service DB URI configuration using standard db names. "
    # afer the database and app are created, 
    # set the connection string of the app
    # this makes a lot of assumptions about how the app is configured: 
    # 1) the app has been provisioned already, before the database is (not alwasy true)
    # 2) the app uses python sqlalchemy
    # 3) the app config env variable is SQLALCHEMY_DATABASE_URI
    # 4) and that the app configuration reads from environment variables
    AZDBSERVERNAME=${PROJECT}-psql
    DB_NAME=$AZAPPNAME-dev
    DB_ADMIN_NAME=${PROJECT}admin
    # user enters pw from command line
    read -p "Enter password you entered when creating $DB_NAME for $DB_ADMIN_NAME (no quote marks please) or ctrl+c to cancel...  " DB_ADMIN_PW

    APPDBCONN=postgresql://${DB_ADMIN_NAME}%40${AZDBSERVERNAME}:${DB_ADMIN_PW}@${AZDBSERVERNAME}.postgres.database.azure.com:5432/$DB_NAME

    az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME \
    --settings SQLALCHEMY_DATABASE_URI=$APPDBCONN
}

az_app_database_delete () 
{
    AZDBSERVERNAME=$PROJECT-psql
    DB_NAME=$AZAPPNAME-dev

    echo "Deleting PG Server $AZDBSERVERNAME and all data on it"
    az postgres server delete --resource-group $AZRG \
        --name $SERVER_NAME \

}
