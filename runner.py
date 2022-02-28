# runner.py
# run model code from command line, seperate from the Flask application
# save the outputfiles, or as written currently, just save the HTML file putting together the results
# TODO : incorporate this into the flask command line using click per Flask docs
#        eg.  flask run; flask test; flask run_model <params>

# import model code from the same module used by the flask application
# from app import models #.models import intial_ID_convert, run_model, make_results_html, alter_validation_df, make_validation_df
# from app.models import data_path, max_num_genes
import argparse
import os, sys
from mljob import geneplexus

def read_input_gene_file(filename):
    """ convert file to array of input gene ids
    copied directly from app/views.py  """
    # TODO move this into the job or geneplexus  module

    with open(filename) as genefile:
        string = genefile.read()
    # remove any single quotes if they exist
    no_quotes = string.translate(str.maketrans({"'": None}))
    #input_genes_list = no_quotes.split(",") # turn into a list
    input_genes_list = no_quotes.splitlines()  # turn into a list
    input_genes = [x.strip(' ') for x in input_genes_list] # remove any whitespace
    return(input_genes)

if __name__ == "__main__":

    #TODO send these args in a single package e.g. JSON
    ### gather args
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_path',
                        default='.',
                        type=str,
                        help='folder to save the output data files')
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

    # setup logger
    import logging
    import sys
    logging.basicConfig(format='%(message)s', stream=sys.stderr, level=logging.INFO)



    #### run it
    # TODO save args in a log file, perhaps from stderr

    input_genes = read_input_gene_file(filename=args.gene_file)
    print(f"processing {len(input_genes)} input genes", file=sys.stderr)
    # in models module, data_path is a global var, so set it here

    # set additional config (if needed) available for geneplexus ML
    from dotenv import load_dotenv
    load_dotenv()

    # this is a module-level var that must be set prior to running
    geneplexus.data_path = args.data_path
    # run and save the html.  this command has by-product of also saving data files
    html = geneplexus.run_and_render(input_genes, net_type=args.net_type,
               features=args.features, GSC=args.GSC, jobname=args.jobname,
               output_path=args.output_path)
               

    print(html)
