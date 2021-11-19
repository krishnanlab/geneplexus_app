The "Logic App" here opens a http endpoint. 

The flask app hits that endpoint with JSON data

the logic app then takes the JSON data and creates an Azure Container instance based on some of that JSON data,
and additionally uses that JSON to set ENV variables that the container instance sends into the 
container image when it runs (e.g. Docker -e ).  Those vars are used by the code in the container as input params. 

The logic app was created via the Azure portal and I don't know how to create it back with the CLI

For logic apps to be able to create resources, there needs to be an "api connection" resource in the resource group. 
this api connection is a "Microsoft.Web/connections" resource. 

The api connection and/or the logic app require this app which has the identity of the account that authorizes the 
logic app to create resources.   Currently this api connection is called "aci" which is not a good name.   
files in this folder (for now)

  * logicapp_template.json
    exported ARM template from the portal of the "runmodel" logic app.  This template refers to the api connection which is called "aci"
    and that is hard-coded in the template (so it must exist first?)

  * run_model_logicapp_azuretemplate.json
    just the code portion of the logic app ("Code View" in the portal) I believe this is included in the logicapp_template.json

  * aci_api_connection.json
    exported template for the api connection ("Microsoft.Web/connections")

  * runmodel_logicapp_inputschema.json
    when creating a logica app that accepts JSON, you need to provide a JSON schema of that input.  
    This is the JSON schema for the logic app inputs.  This is also embedded in the Logic App ARM template 
    `"triggers": {"manual": { "type": "Request", "kind": "Http", "inputs": { "schema": { <JSONschema> } } } }`

  * runmodel_logicapp_exampleinputs.json
    example of the JSON that the Flask app needs to construct and send to the logica app HTTP endpoint


Create the API connection
---

Creating an API connecgtino via template : https://medium.com/@derek_li/create-api-connection-via-arm-template-b018e8069808
It seems like most of the examples for this require you to go to a URL and log-in, which is not ideal. 

Creating a logic app from CLI (in preview ):

https://docs.microsoft.com/en-us/azure/logic-apps/quickstart-logic-apps-azure-cli

Create a logic app with CLI
---

https://docs.microsoft.com/en-us/azure/logic-apps/quickstart-logic-apps-azure-cli

MS example: 

`az logic workflow create --resource-group "testResourceGroup" --location "westus" --name "testLogicApp" --definition "testDefinition.json"`

For our CLI system

```bash
AZ_APPDEFINITIONFILE="az_logicapp_definition.json"

envsubst < az_logicapp_definition.json.bash > az_logicapp_definition.json
az logic workflow create --resource-group "$AZRG" --location "$AZLOCATION" \
    --name "$PROJECT-logic-$PROJECTENV" --definition "$AZ_APPDEFINITIONFILE"  \
    --tags $AZTAGS
```

However this logic app definition has a parameter

```json
"parameters": {
        "$connections": {
            "value": {
                "aci": {
                    "connectionId": "/subscriptions/{subcription_id}/resourceGroups/ADSkrishnanlabgeneplexusDev/providers/Microsoft.Web/connections/aci",
                    "connectionName": "aci",
                    "id": "/subscriptions/{subcription_id}/providers/Microsoft.Web/locations/northcentralus/managedApis/aci"
                }
            }
        }
    }
```

to make this work need ARM template + params
make the parms file with bash, deplohy template + parrams file with cli
https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/deploy-cli

```bash

export AZSUBID=$(az account show --query id --output tsv)
export AZLOCATION=centralus
# fill in the ARM template param file with values from the shell
# note this only works in the param file, the template file uses $ which would be replace with blanks
envsubst < az_logicapp_parameters.json.bash > az_logicapp_parameters.json

az deployment group create \
  --name $PROJECT_logicapp_deployment \
  --resource-group $AZRG \
  --template-file logicapp_template.json \
  --parameters @az_logicapp_parameters.json \
  --handle-extended-json-format

```

  * the subid is a paraameter to the template, so it must use a params file
  * can't use the CLI that only uses a definition file json, because that can't be parameterized?
  * have to use ARM templates and use the CLI to deploy the ARM template + param file 
  * I think  this assumes that a "connection" or "api connection" exists called "aci" eg. vi the ID, so 
    * first create the api connection using the VARS?  Or does this put it here for us
    
    * insert this parameter code into this file before running the CLI command above, somehow with BASH



### more info on logic app types: standard vs consuption

There are (at least ) two typees of logic apps 

https://docs.microsoft.com/en-us/azure/logic-apps/single-tenant-overview-compare

https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-overview#logic-app-concepts

Automate deployment for Azure Logic Apps by using Azure Resource Manager templates: https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-azure-resource-manager-templates-overview

Logic App Azure Resource Manager template: https://github.com/Azure/azure-quickstart-templates/blob/master/quickstarts/microsoft.logic/logic-app-create/azuredeploy.json

note that the ARM template in the example and in the documentation "apiVersion": "2019-05-01" BUT when exporting from Portal the  "apiVersion": "2017-07-01" 
which is not listed in the Logica App arm template documentation at all ( there is 2016, 2018, 2019 only ).   Where are the docs?!?



