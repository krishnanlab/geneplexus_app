#!/usr/bin/env python

import glob, shutil, os

"""Copy Validation Data Method
The validation step requires some data files from "backend_data" but not all.   Testing
shows that the validation runs much faster when the data is on the same disk as the application, 
instead of mounted storage.  This python code reads in the application configuration from 
mounted to storage to a folder on the local disk"""
# copy validation data sets
def copy_validation_data(config):

    root_path="/home/site"
    local_data_dir=config['DATA_PATH'] # f"{root_path}/data_backend"
    mounted_path=os.path.join(root_path,"")
    data_file_sets = [
        "ID_conversion/Homo_sapiens__*-to-Entrez__All-Mappings.pickle",
       "/Node_Orders/*_nodelist.txt"]

    for data_file_set in data_file_sets:
        fspath, fsglob = os.path.split(data_file_set)
        dest_dir = os.path.join(local_data_dir, fspath)

        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
        
        for file_in_storage in glob.glob(os.path.join(config["STORAGE_PATH"],data_file_set)):
            shutil.copy(file_in_storage, dest_dir)



if __name__ == "__main__":
    # import app to get the config
    config = {}
    config['DATA_PATH']="/home/site"
    config['STORAGE_PATH']="/home/site/"
    copy_validation_data(config)

