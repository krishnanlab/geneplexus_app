# Geneplexus Web Server: Installing the application locally

These instructions are for internal developers to get started working ont his sytem and running it locally.   The author do not currently provide support for this outside of the team members.   

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

    - For the system to send emails, config the email service. See [EMAIL.md](EMAIL.md) documention for details

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

## Testing the model run

The model is run from methods in `models.py` which are encapsulated in a wrapper script `runner.py` which accepts command line parameters, and is used by the back-end container.   You can run a test job by sending the parameters like
```sh
source .env
python test/runner.py --output_path $OUTPUT_PATH --net_type BioGRID --features Embedding --GSC GO -j $JOBNAME -d $DATA_PATH  $GENE_FILE > $OUTPUT_FILE
```

There is a shell script that does all this for you, and as set of test genes, in the `/test` folder.   You must have set `DATA_PATH` and `JOB_PATH` to valide folders in `.env`  (or modify the script).  From the top project folder, run

```sh
test/test_runner_py.sh
```

it will create a new folder inside `$JOB_PATH` to hold the job output.  

Note there is (currently) no route/method in that app to run a job locally from inside the apap e.g. in a `flask run` , but there should be~ 
