# runner.py
# run model code from command line, seperate from the Flask application
# save the outputfiles, or as written currently, just save the HTML file putting together the results
# TODO : incorporate this into the flask command line using click per Flask docs
#        eg.  flask run; flask test; flask run_model <params>

# import model code from the same module used by the flask application
from app.models import intial_ID_convert, run_model, make_template, alter_validation_df, make_validation_df
from app.models import file_loc, data_path, max_num_genes

import argparse, warnings
import os

def read_input_gene_file(filename):
    """ convert file to array of input gene ids
    copied directly from app/views.py """

    with open(filename) as genefile:
        string = genefile.read()
    # remove any single quotes if they exist
    no_quotes = string.translate(str.maketrans({"'": None}))
    #input_genes_list = no_quotes.split(",") # turn into a list
    input_genes_list = no_quotes.splitlines()  # turn into a list
    input_genes = [x.strip(' ') for x in input_genes_list] # remove any whitespace
    return(input_genes)


def run(gene_file, data_path, net_type='BioGRID', features='Embedding', GSC='GO', job="jobrunner"):
    """run from input file to completion (HTML results) """
    
    # suppress unecessary warnings to avoid mixing them with html output
    warnings.filterwarnings('ignore')
    # data_path and fileloc are global vars in models.py
    # used by all methods that open files
    # normally set by app.config, setting manually here from CLI arg

    # data_path = args.data_path
    file_loc = 'local'

    # 1. read gene file and convert it
    input_genes = read_input_gene_file(filename=gene_file)
    convert_IDs, df_convert_out = intial_ID_convert(input_genes)
    df_convert_out, table_info = make_validation_df(df_convert_out)
    # this is in views.py, but not used by make_template()
    # df_convert_out_subset, table_info_subset = alter_validation_df(
    #     df_convert_out, table_info,
    #     net_type=args.net_type)

    # 2. run model
    # TODO : modify these functions to check for valid inputs and raise errors if not correct
    #        input validation should be done in the method that uses the input, not here
    graph, df_probs, df_GO, df_dis, avgps = run_model( convert_IDs=convert_IDs, 
                                                    net_type=net_type, 
                                                    GSC=GSC, 
                                                    features=features )

    # TODO : write all of these to disk if we want to change the presentation or review for debugging

    # 3. generate html of results visualization
    html = make_template(job, net_type, features, GSC, 
                         avgps, df_probs, df_GO, df_dis, 
                         df_convert_out, table_info, graph)

    return(html)


if __name__ == "__main__":

    ### gather args
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--net_type',
                        default='BioGRID',
                        type=str,
                        help='options are BioGRID, STRING-EXP, STRING, GIANT-TN')
    parser.add_argument('-f', '--features',
                        default='Embedding',
                        type=str,
                        help='options are Embedding, Adjacency, Influence')
    parser.add_argument('-g', '--GSC',
                        default='GO',
                        type=str,
                        help='options are GO, DisGeNet')

    parser.add_argument('-j', '--jobname',
                        default='jobrunner',
                        type=str,
                        help='jobname sets the name of the folder to read/write to')

    parser.add_argument('-d', '--data_path',
                        default='./',
                        type=str,
                        help='path with the backend data files are located')
    # cross validation - allow for two ways to indicate if we are doing CV
    parser.add_argument('-cv',     '--cross_validation',
                        dest='CV', action='store_true')
    parser.add_argument('--no-cv', '--no_cross_validation',
                        dest='CV', action='store_false')
    parser.set_defaults(CV=True)
    # the final arg is just the filename of the genefile to read in
    parser.add_argument('gene_file')

    args = parser.parse_args()


    #### run it
    # TODO save args in a log file, perhaps from stderr


    # # data_path and fileloc are global vars in models.py
    # # used by all methods that open files
    # # normally set by app.config, setting manually here from CLI arg
    # data_path = args.data_path
    # file_loc = 'local'


    # # 1. read gene file and convert it
    # input_genes = read_input_gene_file(filename=args.genefile)
    # convert_IDs, df_convert_out = intial_ID_convert(input_genes)
    # df_convert_out, table_info = make_validation_df(df_convert_out)
    # # this is in views.py, but not used by make_template()
    # # df_convert_out_subset, table_info_subset = alter_validation_df(
    # #     df_convert_out, table_info, 
    # #     net_type=args.net_type)

    # # 2. run model 
    # # TODO : modify these functions to check for valid inputs and raise errors if not correct
    # #        input validation should be done in the method that uses the input, not here
    # graph, df_probs, df_GO, df_dis, avgps = run_model(convert_IDs, net_type=args.net_type, features=args.features, GSC=args.GSC) #, data_path=args.data_path)

    # # TODO : write all of these to disk if we want to change the presentation or review for debugging

    # # 3. generate html of results visualization
    # html = make_template(job=args.jobname,  net_type=args.net_type, features=args.features, GSC=args.GSC, 
    #               avgps=avgps, df_probs=df_probs, df_GO=df_GO, df_dis=df_dis, 
    #               df_convert_out=df_convert_out, table_info=table_info, graph=graph)


    html = run(gene_file = args.gene_file, data_path=args.data_path, net_type=args.net_type,
               features=args.features, GSC=args.GSC, job=args.jobname)

    print(html)
