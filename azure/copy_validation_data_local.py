#!/usr/bin/env python

import glob, shutil, os
from dotenv import load_dotenv

"""Copy Validation Data Method
The validation step requires some data files from "backend_data" but not all.   Testing
shows that the validation runs somwewhat faster when the data is on the same disk as the application, 
instead of reading it from mounted storage.  This python code reads in the application configuration from 
mounted to storage to a folder on the local disk.  After running this from the azure app service 
bash or ssh, update the app service configuration to point to the folder you create on the app service disk

In addition, for this to work, you must have 'persistant storage' turned on in the app service (otherwise
the files you copy will be lost when the app service cycles)"""

# copy validation data sets
def copy_validation_data(mounted_data_dir, local_data_dir):
    """copy specific backend files used by geneset validation from mounted to local paths

    Consider using the config object from the app to retrieve the local_data_dir = config['DATA_PATH']
    """

    data_file_sets = [
        "ID_conversion/Homo_sapiens__*-to-Entrez__All-Mappings.pickle",
       "/Node_Orders/*_nodelist.txt"]

    for data_file_set in data_file_sets:
        fspath, fsglob = os.path.split(data_file_set)
        dest_dir = os.path.join(local_data_dir, fspath)

        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        
        for file_in_storage in glob.glob(os.path.join(mounted_data_dir,data_file_set)):
            shutil.copy(file_in_storage, dest_dir)


if __name__ == "__main__":
    # import app to get the config
    load_dotenv('.env')
    local_data_dir=os.getenv("DATA_PATH", "/home/site/backend")
    # this next value is totally dependent on how the azure process mounts the storage, 
    # see azure/azuredeploy.sh and edit this as needed
    mounted_data_dir = "/home/site/geneplexus-files-dev//data_backend2"
    copy_validation_data(mounted_data_dir, local_data_dir)
    


