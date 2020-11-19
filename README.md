# geneplexus_app
### This is the code for the frontend of the GenePlexus webserver
#
### Installing the application locally
1. **Clone the repo**<br>
   git clone https://github.com/krishnanlab/geneplexus_app.git
   
2. cd geneplexus_app

3. **Create the virtual environment**<br>
   python -m venv venv
   
4. **Activate the environment**<br>
   Windows<br>
   .\venv\Scripts\activate
 
   Mac<br>
   Source venv/bin/activate

5.  **Install the required packages**<br>
    pip install -r requirements.txt
    
6.  **Download local data using the instructions under "Backend Data" below**

7.  flask run    
    
### Input File
The file "input_genes.txt" has been included in the root folder of the application to use as a sample input
##
### Backend Data
The application will not work without at least a subset of the backend data, which is available on the HPCC at the following location.
##
/mnt/research/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend
##
The "data_backend" folder will need to be created under the "app" folder within the application folder structure
##
Beneath the "data_backend" folder on the HPCC  are several subfolders (e.g. GSCs, Edgelists, Node_Orders, etc).  At a minimum the entire contents of the "ID_conversion" folder will need to be downloaded.  Additionally, any files from the remaining folders that contain the name of the corresponding Network, Feature and Negative Class you want to be able to run.
##
For example, if you want to run the "BioGRID" network with the "Embedding" feature and the "DisGeNet" negative class every file with those attributes in the name of the file will need to be downloaded.  (NOTE: The above example is a good place to start for the minimum files to download) 