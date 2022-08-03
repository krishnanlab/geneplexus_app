# Geneplexus Web application and ML runner

## Using Terraform to create Azure resources to run the application

*This is a draft document where we are collecting the commands needed and will be filled out for readability*

Currently the Terraform file only creates resources for the ML Job running Azure Function app and associated resources.  The Azure web app 
is not included in Terraform but will be


###Components: 

`main.tf` : the only terraform file to run, contains all variable declarations

`example-tfvars.txt` : copy this to a new file, typically named after the suffix it uses.  e.g. dev.tfvars
    * note tfvars files are kept out of git as they can contain sensitive information*

`file_share.sh` :  some aspects of the Azure setup are done with the Azure `az` command line and using external variables. 
    this script will attach existing geneplexux storage (for jobs and data 'backend') to the function app so that 
    inputs and outputs from Geneplexus can be shared between the web application and the process that runs the jobs

Other directories such as `.terraform` and `*.out` files are created when running terraform and are not put into the git repository.  

### Working it

See Terraform website for installation instructions

**First time run**

```
cd Terraform
terraform init
```

**Creating Resources**

edit example-tfvars.txt and save in a new file.   Change your user namne, and the suffix of the resource group you will create

Ensure that the `env` entry is added and unless you want to overwrite existing resources, must be unique.    The resoruce group and
the names of many resources are created by combining `project` and `env` vars. 

`cp example-tfvars.txt dev99.tfvars`  and then edit dev99.tfvars


```
terraform plan -var-file=dev99.tfvars -out dev99.out
terraform apply "dev.out"
```

**Linking Storage**

Run the script in the terraform directory

```
cd Terraform # if you haven't already
source ./file_share.sh
```

**Cleaning House**

To remove all the resources you've created run.  use the same tfvars file you used above

`terraform destroy -var-file=dev99.tfvars`

**Running Functions**

This Terraform script currently does not deploy the python code to the function app, it only creates the resources. 
See the README in `mljob` folder for directions on how to "deploy" the code to the Azure resources that this Terraform creates.  

