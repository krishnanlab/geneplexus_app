import json

import numpy as np
import pandas as pd

from flask import current_app
data_path = current_app.config.get("DATA_PATH")

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