import json
import numpy as np
import pandas as pd
import pickle
import warnings
from scipy.stats import hypergeom
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import average_precision_score
from scipy.spatial.distance import cosine
from scipy.stats import rankdata

from jinja2 import Environment, FileSystemLoader

import os, logging

# for serializing output
from mljob.model_output import save_output

from geneplexus import geneplexus


# these are currently global vars within this module
# to keep this module independent from the flask app, they
# are declared here, but set_config is called when the app is created. 
file_loc = "local"
data_path = "../data_backend2/" 
max_num_genes = 50 

def set_config(app_config):
    """set the global vars for this module from a config dictionary from an app or otherwise
    Only override those defaults if the setting is in the config, allowing partial config"""
    if app_config.get("FILE_LOC"):
        file_loc = app_config.get("FILE_LOC")
    if app_config.get("DATA_PATH"):    
        data_path = app_config.get("DATA_PATH")
    if app_config.get("MAX_NUM_GENES"):
        max_num_genes = app_config.get("MAX_NUM_GENES")



################################################################################################################################

# This set of functions is for running the main parts of the pipeline
    
def make_graph(df_edge, df_probs):
    df_edge.fillna(0)
    df_edge.columns = ['source', 'target', 'weight']
    nodes = df_probs[0:max_num_genes]
    nodes.rename(columns={'Entrez': 'id', 'Class-Label': 'Class'}, inplace=True)
    nodes = nodes.astype({'id': int})

    graph = {}
    graph["nodes"] = nodes.to_dict(orient='records')
    graph["links"] = df_edge.to_dict(orient='records')

    return graph

def run_model(convert_IDs, net_type, GSC, features, logger = logging.getLogger(__name__)):
    gp = geneplexus.GenePlexus(data_path, net_type, features, GSC)
    gp.load_genes(convert_IDs)
    mdl_weights, df_probs, avgps = gp.fit_and_predict()
    df_sim_go, df_sim_dis, weights_go, weights_dis = gp.make_sim_dfs()
    df_edge, isolated_genes, df_edge_sym, isolated_genes_sym = gp.make_small_edgelist()
    graph = make_graph(df_edge, df_probs)
    df_convert_out, positive_genes = gp.alter_validation_df()
    return graph, df_probs, df_sim_go, df_sim_dis, avgps, df_edge, df_convert_out, positive_genes
                            
def run_and_render(input_genes,  
                    net_type='BioGRID', features='Embedding', GSC='GO', 
                    jobname="jobrunner", output_path = None, logger = logging.getLogger(__name__)
                    ):
    
    """generate the output html from input genes to completion, eg combine.  
    Params: 
    input_genes : validated list of genes (as read from file) 
    data_path : location on disk of backend data needed for model
    net_type, features, GSC : model params
    jobname : name of this 'run' to put into output html
    output_path : optional folder to save the output as we go.  If 'None', then don't save the output
    logger : optional logging system to use for output.  defaults to the logger for the application, if one

    """
    # TODO add a check that the backend data is present in data_path

    # suppress unecessary warnings generated in model code
    #  to avoid putting them in stdout or stderr, which are used for logging
    warnings.filterwarnings('ignore')
    
    # run model, assumes data_path global is set correctly
    graph, df_probs, df_GO, df_dis, avgps, df_edgelist, df_convert_out, positive_genes = run_model(input_genes, net_type, GSC, features, logger)
    input_count = df_convert_out.shape[0]
    # save output if a path was provided, using methods from model_output module
    # 
    if ( output_path and os.path.exists(output_path) ):
        job_info = save_output(output_path, jobname, net_type, features, GSC, avgps, input_count, positive_genes, 
    df_probs, df_GO, df_dis, df_convert_out, graph, df_edgelist)
    data = {
        'jobname': jobname,
        'network': net_type,
        'feature': features,
        'negative': GSC,
        'avgps': avgps,
    }
    jsonHeaders = {'Content-type': 'application/json'}
    import requests
    status_code = requests.post('http://127.0.0.1:5000/update_result',
                            json=data)
    print(status_code.json())


#######################################################################################################################

# This set of functions is for abstracting how a file is loaded
# IMPORTANT: The file paths differ from the the utls.py file in GenePlexusBackend.
#            Do not simple copy over from that file

#######################################################################################################################
