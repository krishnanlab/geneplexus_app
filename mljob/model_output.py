""" this module is to save and read from output from Dr. Chris Mancuso's GenePlexus Model code, to allow 
for change in implementation without changing the model code, the runner or Flask application code"""

import os, sys
import json

def save_output(output_path, jobname, net_type, features, GSC, avgps, input_count, positive_genes, 
    df_probs, df_GO, df_dis, df_convert_out_subset, graph):

    # save all data frames to files in standard format
    df_probs_file = save_df_output(output_path, jobname, 'df_probs', df_probs)
    df_GO_file = save_df_output(output_path, jobname, 'df_GO',df_GO )
    df_convert_out_subset_file = save_df_output(output_path, jobname, 'df_convert_out_subset', df_convert_out_subset)
    df_dis_file = save_df_output(output_path, jobname, 'df_dis',df_dis)

    # the 'graph' is a dict of dicts (node, edges), so just save as json
    graph_file = construct_output_filename(jobname, 'graph', 'json')
    graph_file_path = construct_output_filepath(output_path, jobname, graph_file)
    with open(graph_file_path, 'w') as gf:
        json.dump(graph, gf)

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
        'graph_file':  graph_file
        }

    print(job_info, file=sys.stderr)
    
    job_info_path = construct_output_filepath(output_path, jobname, 'job_info', ext = 'json')
    print(f"saving job info to {job_info_path} ",file=sys.stderr)   
    with open(job_info_path, 'w') as jf:
        json.dump(job_info, jf)

    return(job_info)


def save_df_output(output_path, jobname, output_name, output_df):
    """ save data frames from model runs in a consistent way"""
    output_filename = construct_output_filename(jobname, output_name, '.tsv')
    output_filepath=construct_output_filepath(output_path, jobname, output_filename)
    output_df.to_csv(path_or_buf = output_filepath, sep = '\t', index = False, line_terminator = '\n')
    return(output_filename)

    
def read_output(output_path, jobname):
    """retrieve the info about the job, but don't read in data frames"""
    job_info_file = construct_output_filepath(output_path, jobname, 'job_info', ext = 'json')
    if os.path.exists(job_info_file):
        job_info = json.load(job_info_file)
        return(job_info)
    else:
        print(f"job info file not found: {job_info_file} ",file=sys.stderr)
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

    output_file_path = os.path.join(output_path, output_name +  ext)
    return(output_file_path)

