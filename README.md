## GenePlexus Web Application

The GenePlexus webserver enables researchers to predict novel genes similar to their genes of interest based on their patterns of connectivity in human genome-scale molecular interaction networks.

This code is an internal project to run a 'front-end' web application ( python flask application ) that collects a gene set and parameter selections to run the model building code.    The main focus on this application is to run model for producing novel gene probabilities using cloud technology. 

This app is under development  

### Installing the application locally

1. **Clone the repo**<br>
```
   git clone https://github.com/krishnanlab/geneplexus_app.git
   cd geneplexus_app
```
2. **Create the virtual environment**<br>
   `python -m venv venv ` or `conda create -n geneplexus_app`

    and activate it
   
   `.\venv\Scripts\activate` or `conda activate geneplexus_app`
 

3.  **Install the required packages**

    `pip install -r requirements.txt`
    
4.  **Download local data using the instructions under "Backend Data" below**   If you are on-campus, you can instead
   mount a SMB connection to 

5.  create a .env file

    - must have two entries to run the front-end (with gene validation): 

```
JOB_PATH=/path/to/job/files
DATA_PATH=/path/to/backend/datafiles
```

    - For the system to send emails, config the email service. See [EMAIL.md](email.md) documention for details

```
NOTIFIER_EMAIL_ADDRESS='app@geneplexus.net'  # the address from which the app sends emails, 
                                             # and that's configured in sendgrid 
SENDGRID_API_KEY='some key '                 # get this from our sendgrid.com account
TEST_EMAIL_RECIPIENT='you@youraddress.com'             # the email recipient you'd like to use for testing
```


6.  flask run    
    
### Input File
The file "input_genes.txt" has been included in the root folder of the application to use as a sample input


### Backend Data
The application will not work without at least a subset of the backend data, which is available on the HPCC at the following location.

`/mnt/research/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend2`

The "data_backend2" folder will need to be created under the "app" folder within the application folder structure

Beneath the "data_backend" folder on the HPCC  are several subfolders (e.g. GSCs, Edgelists, Node_Orders, etc).  At a minimum the entire contents of the "ID_conversion" folder will need to be downloaded.  Additionally, any files from the remaining folders that contain the name of the corresponding Network, Feature and Negative Class you want to be able to run.

For example, if you want to run the "BioGRID" network with the "Embedding" feature and the "DisGeNet" negative class every file with those attributes in the name of the file will need to be downloaded (in the same folder structure/names) (NOTE: The above example is a good place to start for the minimum files to download) 

## Run on Cloud

The goal of this project is to run as efficiently (i.e cheaply) as possible and since buillding and running the model against the gene networks is computationally intensive, the cloud architecture runs those like batch jobs away from the web server.   

Using Micrososft Azur cloud, the approach we took is to create and run the model in a container instance on demand, which keeps the web application small, and uses compute only when needed.  

To build all the resources needed for this architecture, see the    `/auzre` folder and the readme in that folder for instructions to run the `azuredeploy.sh` shell script which uses the Azure CLI and ARM templates.    Some manual intervention is necessary to complete the process.   The script creates resources with a suffix on t Once the resources are there, you must the use `git push` to the Azure web application git deployment URL to upload the App code into the App Service., and subsequent code changes and be git-pushed to the App service without having to rebuild anything. 

 