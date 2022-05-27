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

def intial_ID_convert(input_genes):
    # load all the possible conversion dictionaries
    convert_types = ['ENSG', 'Symbol', 'ENSP', 'ENST']
    all_convert_dict = {}
    for anIDtype in convert_types:
        convert_tmp = load_dict('to_Entrez', anIDtype_=anIDtype)
        convert_tmp = {akey.upper():convert_tmp[akey] for akey in convert_tmp}
        all_convert_dict[anIDtype] = convert_tmp

    # make some place holder arrays
    convert_IDs = []  # This will be a flat list for Entrez IDs to use as positives
    convert_out = []  # This will be a list of lists that will be used to tell user the conversions made
    for agene in input_genes:
        try:
            agene_int = int(agene)
            convert_out.append([agene_int, agene_int])
            convert_IDs.append(agene_int)
        except ValueError:
            for idx, anIDtype in enumerate(convert_types):
                if agene in all_convert_dict[anIDtype]:
                    convert_IDs = convert_IDs + all_convert_dict[anIDtype][agene]
                    convert_out.append([agene, ', '.join(all_convert_dict[anIDtype][agene])])
                    break
                elif idx == len(convert_types) - 1:
                    convert_out.append([agene, 'Could Not be mapped to Entrez'])
    df_convert_out = pd.DataFrame(convert_out, columns=['Original_ID', 'ID_converted_to_Entrez'])
    df_convert_out = df_convert_out.astype({'Original_ID': str, 'ID_converted_to_Entrez': str})
    return convert_IDs, df_convert_out


def make_validation_df(df_convert_out):
    table_summary = []
    #num_converted_to_Entrez = df_convert_out[~(df_convert_out['ID_converted_to_Entrez']=='Could Not be mapped to Entrez')].shape[0]
    edge_counts = {'BioGRID': 484356,'STRING': 5521113,'STRING-EXP': 2121428,'GIANT-TN': 38904929}
    input_count = df_convert_out.shape[0]
    converted_genes = df_convert_out['ID_converted_to_Entrez'].to_numpy()
    for anet in ['BioGRID','STRING','STRING-EXP','GIANT-TN']:
        net_genes = load_txtfile('net_genes',net_type_=anet)
        df_tmp = df_convert_out[df_convert_out['ID_converted_to_Entrez'].isin(net_genes)]
        pos_genes_in_net = np.intersect1d(converted_genes,net_genes)
        table_row = {'Network': anet, 'NetworkGenes': len(net_genes), 'NetworkEdges': edge_counts[anet], 'PositiveGenes': len(pos_genes_in_net)}
        table_summary.append(dict(table_row))
        tmp_ins = np.full(len(converted_genes),'N',dtype=str)
        tmp_ins[df_tmp.index.to_numpy()] = 'Y'
        df_convert_out['In %s?'%anet] = tmp_ins

    df_convert_out = df_convert_out.rename(columns = {'Original_ID': 'Original ID', 'ID_converted_to_Entrez': 'Entrez ID'})

    return df_convert_out, table_summary, input_count
    
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

#######################################################################################################################

# This set of functions is for abstracting how a file is loaded
# IMPORTANT: The file paths differ from the the utls.py file in GenePlexusBackend.
#            Do not simple copy over from that file

#######################################################################################################################

def load_txtfile(file_type, dtype_=str, net_type_=None, GSC_=None, target_set_=None):
    if file_type == 'net_genes':
        output_txt = np.loadtxt(f'{data_path}NodeOrder_{net_type_}.txt', dtype=dtype_)

    elif file_type == 'uni_genes':
        output_txt = np.loadtxt(f'{data_path}GSCs/{GSC_}_{net_type_}_universe.txt', dtype=dtype_)

    elif file_type == 'GSC_order':
        output_txt = np.loadtxt(f'{data_path}CorrectionMatrices/{target_set_}_{net_type_}_Orders.txt', dtype=dtype_)

    return output_txt


def load_dict(file_type, anIDtype_=None, GSC_=None, net_type_=None, target_set_=None, features_=None):
    if file_type == 'to_Entrez':
        with open(f'{data_path}IDconversion_Homo-sapiens_{anIDtype_}-to-Entrez.json', 'r') as handle:
            output_dict = json.load(handle)

    elif file_type == 'good_sets':
        with open(f'{data_path}GSC_{GSC_}_{net_type_}_GoodSets.json', 'r') as handle:
            output_dict = json.load(handle)

    elif file_type == 'Entrez_to_Symbol':
        with open(f'{data_path}ID_conversion_Homo_sapiens_Entrez-to-Symbol.json', 'r') as handle:
            output_dict = json.load(handle)

    elif file_type == 'Entrez_to_Name':
        with open(f'{data_path}ID_conversion_Homo_sapiens_Entrez-to-Name.json', 'r') as handle:
            output_dict = json.load(handle)

    elif file_type == 'weights':
        with open(f'{data_path}PreTrainedWeights_{target_set_}_{net_type_}_{features_}.json', 'r') as handle:
            output_dict = json.load(handle)
 
    return output_dict
