""" this module is to save and read from output from Dr. Chris Mancuso's GenePlexus Model code, to allow 
for change in implementation without changing the model code, the runner or Flask application code"""

import os, sys
import json
import pandas as pd

def save_output(output_path, jobname, net_type, features, GSC, avgps, input_count, positive_genes, 
    df_probs, df_GO, df_dis, df_convert_out_subset, graph, df_edgelist):

    # TODO : send outputs to save as a dictionary keyed on name.e.g. {'df_probs', df_probs, etc } 
    #        so this module can be more generic.   possibly also add format per item, or use same format for all (JSON or CSV)
    # save all data frames to files in standard format
    df_probs_file = save_df_output(output_path, jobname, 'df_probs', df_probs)
    df_GO_file = save_df_output(output_path, jobname, 'df_GO',df_GO )
    df_convert_out_subset_file = save_df_output(output_path, jobname, 'df_convert_out_subset', df_convert_out_subset)
    df_dis_file = save_df_output(output_path, jobname, 'df_dis',df_dis)
    df_edgelist_file = save_df_output(output_path, jobname, 'df_edgelist', df_edgelist )
    
    # the 'graph' is a dict of dicts (node, edges), so save in different format
    graph_file = save_graph_output(output_path, jobname, graph)

    # copy the results file names into this dictionary (without path) 
    job_info = {
        'jobname': jobname,
        'net_type': net_type,
        'features': features,
        'GSC': GSC,
        'avgps': avgps, 
        'input_count': input_count, 
        'positive_genes': positive_genes,
        'df_probs_file': df_probs_file, 
        'df_GO_file': df_GO_file, 
        'df_dis_file': df_dis_file, 
        'df_convert_out_subset_file': df_convert_out_subset_file, 
        'graph_file':  graph_file,
        'df_edgelist_file' : df_edgelist_file
        }

    print(job_info, file=sys.stderr)
    
    job_info_path = construct_output_filepath(output_path, jobname, 'job_info', ext = 'json')
    print(f"saving job info to {job_info_path} ",file=sys.stderr)   
    with open(job_info_path, 'w') as jf:
        json.dump(job_info, jf)

    return(job_info)

def read_output(output_path, jobname):
    """opposite of writing output, read all output from a job and load into memory """
    
    #TODO : a more generic way to approach this is to save a file of 'job info' which is only a list of file paths with associated types
    #      the read output method then simply reads in each file list in the job_info file into a dictionary with keys for each type
    #      that way the read_output method does not have to explicitly sync'd with the write_output method and the generic job system 
    # writes what ever files needed output, but then writes a file that's a catalog of them.   

    #TODO this may be redundant with methods in jobs.py so reconcile these two modules
    job_info = read_job_info(output_path, jobname)

    if job_info:
        # add new elements to this dictionary to return all data frames in a single dictionary
        # TODO try/catch around these to catch I/O exceptions
        # TODO check if any of these return None and raise an exception if it does
        data_frame_list = ['df_probs','df_GO','df_convert_out_subset','df_dis','df_edgelist']
        for dfname in data_frame_list:
            job_info[dfname] = read_df_output(output_path, jobname, dfname)
    
        job_info['graph'] = read_graph_output(output_path, jobname)
    
    # returns None or empty if no job info was found
    return(job_info)


def save_df_output(output_path, jobname, output_name, output_df):
    """ save data frames from model runs in a consistent way"""
    output_filename = construct_output_filename(jobname, output_name, '.tsv')
    output_filepath=construct_output_filepath(output_path, jobname, output_filename)
    output_df.to_csv(path_or_buf = output_filepath, sep = '\t', index = False, line_terminator = '\n')
    return(output_filename)

def save_graph_output(output_path, jobname, graph):
    """save the data that makes up the network graph to output folder, in JSON format.  
    the 'graph' is a dict of dicts (node, edges), so just save as json"""
    graph_file = construct_output_filename(jobname, 'graph', 'json')
    graph_file_path = construct_output_filepath(output_path, jobname, graph_file)
    with open(graph_file_path, 'w') as gf:
        json.dump(graph, gf)

    return(graph_file)

def read_graph_output(output_path, jobname):
    """ read in a graph as saved by output methoda above"""
    graph_file = construct_output_filename(jobname, 'graph', 'json')
    graph_file_path = construct_output_filepath(output_path, jobname, graph_file)
    with open(graph_file_path, 'r') as gf:
        graph_data = json.load(gf)

    return(graph_data)

def read_df_output(output_path, jobname, output_name):
    """retrieve individual data frames from output folder given the name of the file, assuming they are saved as tsv
    returns: pandas data frame or None if not found
    """
    output_filename = construct_output_filename(jobname, output_name, '.tsv')
    output_filepath = construct_output_filepath(output_path, jobname, output_filename)
    
    if os.path.exists(output_filepath):
        # TODO try /catch
        output_df = pd.read_csv(output_filepath, sep = '\t')
        return(output_df)
    else:
        print(f"output file not found: {output_filepath} ",file=sys.stderr)
        return(None)
    
def read_job_info(output_path, jobname):
    """ read in the job information dictionary"""

    job_info_path = construct_output_filepath(output_path, jobname, 'job_info', ext = 'json')
    if os.path.exists(job_info_path):
        with open(job_info_path) as f:
            job_info = json.load(f)

        return(job_info)
    else:
        print(f"job info file not found: {job_info_path} ",file=sys.stderr)
        return(None)


def construct_output_filename(jobname, output_name, ext = ''):
    """ consistently create output file name from path and job name"""
    # note that when opening a new db files with shelve, it will automatically add .db, so don't add it here"
    if( ext and ext[0] != '.'):
        ext = '.' + ext

    output_file = jobname + '_' +  output_name +  ext
    return(output_file)

def construct_output_filepath(output_path, jobname, output_name, ext = ''):
    """ consistently create output file name from path and job name"""
    # note that when opening a new db files with shelve, it will automatically add .db, so don't add it here"
    if( ext and ext[0] != '.'):
        ext = '.' + ext

    # note this is not currenlty using the job name!  
    #  this is because for the job runner, the full output path for this one job is provided (with the jobname already in it)
    output_file_path = os.path.join(output_path, output_name +  ext)
    return(output_file_path)

