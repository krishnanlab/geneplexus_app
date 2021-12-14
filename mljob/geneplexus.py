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
    input_count = df_convert_out.shape[0]
    converted_genes = df_convert_out['ID_converted_to_Entrez'].to_numpy()
    for anet in ['BioGRID','STRING','STRING-EXP','GIANT-TN']:
        net_genes = load_txtfile('net_genes',net_type_=anet)
        df_tmp = df_convert_out[df_convert_out['ID_converted_to_Entrez'].isin(net_genes)]
        pos_genes_in_net = np.intersect1d(converted_genes,net_genes)
        table_row = {'Network': anet, 'NetworkGenes': len(net_genes), 'PositiveGenes': len(pos_genes_in_net)}
        table_summary.append(dict(table_row))
        tmp_ins = np.full(len(converted_genes),'N',dtype=str)
        tmp_ins[df_tmp.index.to_numpy()] = 'Y'
        df_convert_out['In %s?'%anet] = tmp_ins

    df_convert_out = df_convert_out.rename(columns = {'Original_ID': 'Original ID', 'ID_converted_to_Entrez': 'Entrez ID'})

    return df_convert_out, table_summary, input_count


def alter_validation_df(df_convert_out,table_info,net_type):
    df_convert_out_subset = df_convert_out[['Original ID','Entrez ID','In %s?'%net_type]]
    network = next((item for item in table_info if item['Network'] == net_type), None)
    positive_genes = network.get("PositiveGenes")
    return df_convert_out_subset, positive_genes


def get_genes_in_network(convert_IDs, net_type):
    net_genes = load_txtfile('net_genes', net_type_=net_type)
    pos_genes_in_net = np.intersect1d(np.array(convert_IDs), net_genes)
    genes_not_in_net = np.setdiff1d(np.array(convert_IDs), net_genes)
    return pos_genes_in_net, genes_not_in_net, net_genes


def get_negatives(pos_genes_in_net, net_type, GSC):
    uni_genes = load_txtfile('uni_genes', net_type_=net_type, GSC_=GSC)
    good_sets = load_dict('good_sets', GSC_=GSC, net_type_=net_type)
    M = len(uni_genes)
    N = len(pos_genes_in_net)
    genes_to_remove = pos_genes_in_net
    for akey in good_sets:
        n = len(good_sets[akey]['Genes'])
        k = len(np.intersect1d(pos_genes_in_net, good_sets[akey]['Genes']))
        pval = hypergeom.sf(k - 1, M, n, N)
        if pval < 0.05:
            genes_to_remove = np.union1d(genes_to_remove, good_sets[akey]['Genes'])
    negative_genes = np.setdiff1d(uni_genes, genes_to_remove)
    return negative_genes


def run_SL(pos_genes_in_net, negative_genes, net_genes, net_type, features):
    pos_inds = [np.where(net_genes == agene)[0][0] for agene in pos_genes_in_net]
    neg_inds = [np.where(net_genes == agene)[0][0] for agene in negative_genes]
    data = load_npyfile('data', features_=features, net_type_=net_type)

    std_scale = StandardScaler().fit(data)
    data = std_scale.transform(data)
    Xdata = data[pos_inds + neg_inds, :]
    ydata = np.array([1] * len(pos_inds) + [0] * len(neg_inds))
    clf = LogisticRegression(max_iter=10000, solver='lbfgs', penalty='l2', C=1.0)
    clf.fit(Xdata, ydata)
    mdl_weights = np.squeeze(clf.coef_)
    probs = clf.predict_proba(data)[:, 1]

    if len(pos_genes_in_net) < 20:
        avgp = 'Not enough positive genes'
    else:
        avgps = []
        n_folds = 5
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=None)
        for trn_inds, tst_inds in skf.split(Xdata, ydata):
            clf_cv = LogisticRegression(max_iter=10000, solver='lbfgs', penalty='l2', C=1.0)
            clf_cv.fit(Xdata[trn_inds], ydata[trn_inds])
            probs_cv = clf_cv.predict_proba(Xdata[tst_inds])[:, 1]
            avgp = average_precision_score(ydata[tst_inds], probs_cv)
            num_tst_pos = np.sum(ydata[tst_inds])
            prior = num_tst_pos / Xdata[tst_inds].shape[0]
            log2_prior = np.log2(avgp / prior)
            avgps.append(log2_prior)
        avgp = '{0:.2f}'.format(np.median(avgps))
    return mdl_weights, probs, avgp


def make_prob_df(net_genes,probs,pos_genes_in_net,negative_genes):
    Entrez_to_Symbol = load_dict('Entrez_to_Symbol')
    Entrez_to_Name = load_dict('Entrez_to_Name')
    prob_results = []
    for idx in range(len(net_genes)):
        if net_genes[idx] in pos_genes_in_net:
            class_label = 'P'
            novel_label = 'Known'
        elif net_genes[idx] in negative_genes:
            class_label = 'N'
            novel_label = 'Novel'
        else:
            class_label = 'U'
            novel_label = 'Novel'
        try:
            syms_tmp = '/'.join(Entrez_to_Symbol[net_genes[idx]]) #allows for multimapping
        except KeyError:
            syms_tmp = 'N/A'
        try:
            name_tmp = '/'.join(Entrez_to_Name[net_genes[idx]]) #allows for multimapping
        except KeyError:
            name_tmp = 'N/A'
        prob_results.append([net_genes[idx],syms_tmp,name_tmp,probs[idx],novel_label,class_label])
    df_probs = pd.DataFrame(prob_results,columns=['Entrez','Symbol','Name','Probability','Known/Novel','Class-Label'])
    df_probs = df_probs.astype({'Entrez':str,'Probability':float})
    df_probs = df_probs.sort_values(by=['Probability'],ascending=False)
    df_probs['Rank'] = rankdata(1/(df_probs['Probability'].to_numpy()+1e-9),method='min')
    return df_probs, Entrez_to_Symbol


def make_sim_dfs(mdl_weights,GSC,net_type,features):
    dfs_out = []
    for target_set in ['GO', 'DisGeNet']:
        weights_dict = load_dict('weights',file_loc,net_type_=net_type,target_set_=target_set,features_=features)
        if target_set == 'GO':
            weights_dict_GO = weights_dict
        if target_set == 'DisGeNet':
            weights_dict_Dis = weights_dict
        order = load_txtfile('GSC_order',net_type_=net_type,target_set_=target_set)
        cor_mat = load_npyfile('cor_mat',GSC_=GSC,target_set_=target_set,net_type_=net_type,features_=features)
        add_row = np.zeros((1,len(order)))
        for idx, aset in enumerate(order):
            cos_sim = 1 - cosine(weights_dict[aset]['Weights'],mdl_weights)
            add_row[0,idx] = cos_sim
        cor_mat = np.concatenate((cor_mat,add_row),axis=0)
        last_row = cor_mat[-1,:]
        zq = np.maximum(0, (last_row - np.mean(last_row)) / np.std(last_row))
        zs = np.maximum(0, (last_row - np.mean(cor_mat,axis=0)) / np.std(cor_mat,axis=0))
        z = np.sqrt(zq**2 + zs**2)
        results_tmp = []
        for idx2, termID_tmp in enumerate(order):
            ID_tmp = termID_tmp
            Name_tmp = weights_dict[termID_tmp]['Name']
            z_tmp = z[idx2]
            results_tmp.append([ID_tmp,Name_tmp,z_tmp])
        df_tmp = pd.DataFrame(results_tmp,columns=['ID','Name','Similarity']).sort_values(by=['Similarity'],ascending=False)
        df_tmp['Rank'] = rankdata(1/(df_tmp['Similarity'].to_numpy()+1e-9),method='min')
        dfs_out.append(df_tmp)
    return dfs_out[0], dfs_out[1], weights_dict_GO, weights_dict_Dis


def make_small_edgelist(df_probs, net_type, Entrez_to_Symbol):
    # This will set the max number of genes to look at to a given number
    df_edge = load_df('edgelist', net_type_=net_type)
    df_edge = df_edge.astype({'Node1': str, 'Node2': str})
    top_genes = df_probs['Entrez'].to_numpy()[0:max_num_genes]
    df_edge = df_edge[(df_edge['Node1'].isin(top_genes)) & (df_edge['Node2'].isin(top_genes))]
    genes_in_edge = np.union1d(df_edge['Node1'].unique(), df_edge['Node2'].unique())
    isolated_genes = np.setdiff1d(top_genes, genes_in_edge)
    replace_dict = {}
    for agene in genes_in_edge:
        try:
            syms_tmp = '/'.join(Entrez_to_Symbol[agene])  # allows for multimapping
        except KeyError:
            syms_tmp = 'N/A'
        replace_dict[agene] = syms_tmp
    df_edge_sym = df_edge.replace(to_replace=replace_dict)
    # make smae network as above just with gene symbols instead of entrez IDs
    isolated_genes_sym = []
    for agene in isolated_genes:
        try:
            syms_tmp = '/'.join(Entrez_to_Symbol[agene])  # allows for multimapping
        except KeyError:
            syms_tmp = 'N/A'
        isolated_genes_sym.append(syms_tmp)

    return df_edge, isolated_genes, df_edge_sym, isolated_genes_sym

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

def run_model(convert_IDs, net_type, GSC, features, logger = logging.getLogger(__name__)
):

    logger.info('1. get_genese_in_network')
    pos_genes_in_net, genes_not_in_net, net_genes = get_genes_in_network(convert_IDs,
                                                                                net_type)  # genes_not_in_net could be an output file
    logger.info('2. get_negatives')
    negative_genes = get_negatives(pos_genes_in_net, net_type, GSC)

    logger.info('3. run_SL... features=%s, features')
    mdl_weights, probs, avgps = run_SL(pos_genes_in_net, negative_genes, net_genes, net_type, features)

    logger.info('4. get_negatives...')
    negative_genes = get_negatives(pos_genes_in_net, net_type, GSC)

    logger.info('5. make_prob_df...')
    df_probs, Entrez_to_Symbol = make_prob_df(net_genes, probs, pos_genes_in_net, negative_genes)

    logger.info('6. make_sim_dfs...')
    df_GO, df_dis, weights_dict_GO, weights_dict_Dis = make_sim_dfs(mdl_weights, GSC, net_type,
                                                                           features)  # both of these dfs will be displaed on the webserver
    logger.info('7. make_small_edgelist...')
    df_edge, isolated_genes, df_edge_sym, isolated_genes_sym = make_small_edgelist(df_probs, net_type,
                                                                                          Entrez_to_Symbol)
    logger.info('8. make_graph...')
    graph = make_graph(df_edge, df_probs)

    return graph, df_probs, df_GO, df_dis, avgps




def make_results_html(jobname, net_type, features, GSC, 
            avgps, df_probs, df_GO, df_dis, input_count, positive_genes, 
            df_convert_out_subset, graph,
            job_info, row_limit = 500):

    """Render the Jinja template, filling fields as appropriate, not relying on Flask app to be loaded
    params: job details, and outputs data frames from jobs
    params job_info dictionary of job information as returned from 'model_output.save_output()`

    return rendered HTML
    If a dictionary of 'job_info' is sent, then use that to add links to download these files"""
    # Find the module absolute path and locate templates
    
    module_root = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(module_root))

    # Find the absolute module path and the static files
    context_menu_path = os.path.join(os.path.dirname(__file__), 'static', 'd3-v4-contextmenu.js')
    with open(context_menu_path, 'r') as f:
        context_menu_js = f.read()

    tip_path = os.path.join(os.path.dirname(__file__), 'static', 'd3-tip.js')
    with open(tip_path, 'r') as f:
        d3_tip_js = f.read()

    graph_path = os.path.join(os.path.dirname(__file__), 'static', 'graph.js')
    with open(graph_path, 'r') as f:
        graph_js = f.read()

    datatable_path = os.path.join(os.path.dirname(__file__), 'static', 'datatable.js')
    with open(datatable_path, 'r') as f:
        datatable_js = f.read()

    main_path = os.path.join(os.path.dirname(__file__), 'static', 'main.css')
    with open(main_path, 'r') as f:
        main_css = f.read()

    graph_css_path = os.path.join(os.path.dirname(__file__), 'static', 'graph.css')
    with open(graph_css_path, 'r') as f:
        graph_css = f.read()

    d3_tip_css_path = os.path.join(os.path.dirname(__file__), 'static', 'd3-tip.css')
    with open(d3_tip_css_path, 'r') as f:
        d3_tip_css = f.read()

    template = env.get_template('result_base.html').render(
        job_info = job_info,
        jobname=jobname,
        network=net_type,
        features=features,
        negativeclass=GSC,
        avgps=avgps,
        input_count=input_count,
        positive_genes=positive_genes,
        context_menu_js=context_menu_js,
        d3_tip_js=d3_tip_js,
        graph_js=graph_js,
        datatable_js=datatable_js,
        main_css=main_css,
        graph_css=graph_css,
        d3_tip_css=d3_tip_css,
        probs_table=df_probs.head(row_limit).to_html(index=False, classes='table table-striped table-bordered" id = "probstable'),
        go_table=df_GO.head(row_limit).to_html(index=False,
                               classes='table table-striped table-bordered nowrap" style="width: 100%;" id = "gotable'),
        dis_table=df_dis.head(row_limit).to_html(index=False, classes='table table-striped table-bordered" id = "distable'),
        validate_results=df_convert_out_subset.head(row_limit).to_html(index=False,
                                              classes='table table-striped table-bordered" id = "validateresults'),
        graph=graph)
    
    # return utf-8 string
    return(template)
                            
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
    
    # read gene file and convert it
    convert_IDs, df_convert_out = intial_ID_convert(input_genes)

    # prep and validate input, save validation for presentation
    df_convert_out, table_summary, input_count = make_validation_df(df_convert_out)
    df_convert_out_subset, positive_genes = alter_validation_df(df_convert_out,table_summary,net_type)
    
    # run model, assumes data_path global is set correctly
    graph, df_probs, df_GO, df_dis, avgps = run_model(convert_IDs, net_type, GSC, features, logger)

    # save output if a path was provided, using methods from model_output module
    # 
    if ( output_path and os.path.exists(output_path) ):
        job_info = save_output(output_path, jobname, net_type, features, GSC, avgps, input_count, positive_genes, 
    df_probs, df_GO, df_dis, df_convert_out_subset, graph)

    # generate html visualization/report
    results_html = make_results_html(jobname, net_type, features, GSC, avgps, df_probs, df_GO, df_dis,
                                        input_count, positive_genes, df_convert_out_subset, graph, job_info)
    # return HTML file
    return(results_html)

#######################################################################################################################

# This set of functions is for abstracting how a file is loaded
# IMPORTANT: The file paths differ from the the utls.py file in GenePlexusBackend.
#            Do not simple copy over from that file

#######################################################################################################################

def load_txtfile(file_type, dtype_=str, net_type_=None, GSC_=None, target_set_=None):
    if file_type == 'net_genes':
        output_txt = np.loadtxt(f'{data_path}Node_Orders/{net_type_}_nodelist.txt', dtype=dtype_)

    elif file_type == 'uni_genes':
        output_txt = np.loadtxt(f'{data_path}GSCs/{GSC_}_{net_type_}_universe.txt', dtype=dtype_)

    elif file_type == 'GSC_order':
        output_txt = np.loadtxt(f'{data_path}CorrectionMatrices/{target_set_}_{net_type_}_Orders.txt', dtype=dtype_)

    return output_txt


def load_npyfile(file_type, features_=None, net_type_=None, GSC_=None, target_set_=None):
    if file_type == 'data':
        output_npy = np.load(f'{data_path}{features_}/{net_type_}_data.npy')

    elif file_type == 'cor_mat':
        output_npy = np.load(f'{data_path}CorrectionMatrices/{GSC_}_{target_set_}_{net_type_}_{features_}_CorMat.npy')

    return output_npy


def load_df(file_type, sep_='\t', header_=None, net_type_=None):
    if file_type == 'edgelist':

            if net_type_ == 'BioGRID':
                output_df = pd.read_csv(f'{data_path}Edgelists/{net_type_}.edg', sep=sep_, header=header_,
                                        names=['Node1', 'Node2'])
                output_df["Weight"] = 1
            else:
                output_df = pd.read_csv(f'{data_path}Edgelists/{net_type_}.edg', sep=sep_, header=header_,
                                        names=['Node1', 'Node2', 'Weight'])

    return output_df


def load_dict(file_type, anIDtype_=None, GSC_=None, net_type_=None, target_set_=None, features_=None):
    if file_type == 'to_Entrez':
        with open(f'{data_path}ID_conversion/Homo_sapiens__{anIDtype_}-to-Entrez__All-Mappings.pickle','rb') as handle:
            output_dict = pickle.load(handle)

    elif file_type == 'good_sets':
        with open(f'{data_path}GSCs/{GSC_}_{net_type_}_GoodSets.pickle', 'rb') as handle:
            output_dict = pickle.load(handle)

    elif file_type == 'Entrez_to_Symbol':
        with open(f'{data_path}ID_conversion/Homo_sapiens__Entrez-to-Symbol__All-Mappings.pickle','rb') as handle:
            output_dict = pickle.load(handle)

    elif file_type == 'Entrez_to_Name':
        with open(f'{data_path}ID_conversion/Homo_sapiens__Entrez-to-Name__All-Mappings.pickle','rb') as handle:
            output_dict = pickle.load(handle)

    elif file_type == 'weights':
        with open(f'{data_path}PreTrainedModels/{target_set_}_{net_type_}_{features_}_ModelWeights.pickle','rb') as handle:
            output_dict = pickle.load(handle)
 
    return output_dict
