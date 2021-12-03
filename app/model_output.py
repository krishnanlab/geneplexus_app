""" this module is to save and read from output from Dr. Chris Mancuso's GenePlexus Model code, to allow 
for change in implementation without changing the model code, the runner or Flask application code"""

import os.path, shelve

def save_all_output(output_path, job_name, output_data)
    """save the collection of output values (in a dictionary) """
    if not ( output_path and job_name and os.path.exists(output_path)):
        # TODO log! or print to stderr? 
        print("output path not found, did not save output data")
        return(None)

    output_file = os.path.join(output_path, jobname + ".db")
    output_db = shelve.open(construct_output_filename(output_path, jobname))
    for key,value in output_data:
        print(f"saving {key} to {output_file} ")      # TODO log! 
        output_db[key] = value
    
    output_db.close()
    
    return(output_file)

def get_output(output_path, job_name, item_name):
    """ retrieve one item from the output.  For arrays this gets the whole item"""
    output_file = construct_output_filename(output_path, job_name)
    if not os.path.exists(output_file):
        return(None)
    
    output_db = shelve.open(output_file)
    if item_name in output_db:  #TODO use try/catch instead
        return(output_db[item_name])
    
    output_db.close()


def construct_output_filename(output_path, job_name):
    """ consistently create output file name from path and job name"""
    output_file = os.path.join(output_path, jobname + ".db")
    return(output_file)

