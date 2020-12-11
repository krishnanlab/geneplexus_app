#runner.py
# run model code from command line, seperate from the Flask application
# TODO : incorporate this into the flask command line using click per Flask docs
#        eg.  flask run; flask test; flask run_model <params>

# from app import app
# import config


from app.models import intial_ID_convert, run_model, make_template, alter_validation_df, make_validation_df
from app.models import file_loc, data_path, max_num_genes




import argparse
import os
# from dotenv import load_dotenv

# load_dotenv('.env')

# app.config.from_object(config.DevConfig)
# print('data path')
# print(os.getenv('DATA_PATH'))
# print("config")
# print(app.config)

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
                        default='job',
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
    parser.add_argument('genefile')

    args = parser.parse_args()

    # TODO handle arg errors

    #### run it
    print("running with ")
    print(args)
    
    input_genes = read_input_gene_file(filename=args.genefile)
    
    
    # data_path is a global var used in models.py 
    # normally set by app.config, see if we can override with CLI arg
    data_path = args.data_path
    file_loc = 'local'

    convert_IDs, df_convert_out = intial_ID_convert(input_genes)
    print(convert_IDs)

    df_convert_out, table_info = make_validation_df(df_convert_out)
    # df_convert_out_subset, table_info_subset = alter_validation_df(
    #     df_convert_out, table_info, 
    #     net_type=args.net_type)

    

    graph, df_probs, df_GO, df_dis, avgps = run_model(convert_IDs, net_type=args.net_type, features=args.features, GSC=args.GSC) #, data_path=args.data_path)

    # this writes an html file in current dir based on jobname

    make_template(job=args.jobname,  net_type=args.net_type, features=args.features, GSC=args.GSC, 
                  avgps=avgps, df_probs=df_probs, df_GO=df_GO, df_dis=df_dis, 
                  df_convert_out=df_convert_out, table_info=table_info, graph=graph)

    # TODO check if the file was written






    # NOTES
    # the goal of this is to  
    # 1) save html template that can be read by the application 
    # 2) save files that could later be read in by the application to generate a view
        #    return render_template("results.html", tic1=tic1, form=form, graph=graph, avgps=avgps, table_info=table_info_subset,
        #                           probs_table=df_probs.to_html(index=False,
        #                                                        classes='table table-striped table-bordered" id = "probstable'),
        #                           go_table=df_GO.to_html(index=False,
        #                                                  classes='table table-striped table-bordered nowrap" style="width: 100%;" id = "gotable'),
        #                           dis_table=df_dis.to_html(index=False,
        #                                                    classes='table table-striped table-bordered" id = "distable'),
        #                           validate_table=df_convert_out_subset.to_html(index=False,
        #                                                                        classes='table table-striped table-bordered" id = "validatetable')
        #                           )
