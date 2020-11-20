# geneplexus_app

This is the code for the frontend of the GenePlexus webserver

## Installation and Configuration

Strongly recommended to create a new python environment (using venv or anaconda's "conda create --envname `

Install python packages needed using 

`pip install -r requirements.txt`

Create a folder for the data to be used.  The app currently requires the folder app/data_backend

you also must create a .env file, even if it's empty, to run this application

Modify the .env and .flaskenv for your specific needs

## Backend Data

#### The application will not work without at least a subset of the backend data, which is available on the HPCC at the following location.

/mnt/research/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend

The "data_backend" folder will need to be created under the "app" folder within the application folder structure

Beneath the "data_backend" folder on the HPCC  are several subfolders (e.g. GSCs, Edgelists, Node_Orders, etc).  At a minimum the entire "ID_conversion" folder will need to be downloaded into data_backend (maintain the folder names)  Additionally, any files from the remaining folders that contain the name of the corresponding Network, Feature and Negative Class you want to be able to run.

For example, if you want to run the "BioGRID" network with the "Embedding" feature and the "DisGeNet" negative class every file with those attributes in the name of the file will need to be downloaded.  (NOTE: The above example is a good place to start for the minimum files to download) 