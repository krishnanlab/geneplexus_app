from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for
from app.forms import IndexForm, AboutForm
from app import app, models
import pickle
import time

@app.route("/", methods=['GET','POST'])
def index():
    form = IndexForm()

    if request.method == 'GET':

        return render_template("index.html", form=form)

    elif request.method == 'POST':
        # 'genes' exists as a session variable, use that data for subsequent requests
        # if it doesn't, no data has been loaded yet so get the data from a selected file
        #
        # from flask import session
        # session.clear()

        if 'genes' in session:
            input_genes_Entrez = session['genes']
        else:
            f = request.files['input_genes'] # read in the file
            string = f.stream.read().decode("UTF8") # convert the FileStorage object to a string
            no_quotes = string.translate(str.maketrans({"'":None})) # remove any single quotes if they exist
            input_genes_list = no_quotes.split(",") # turn into a list
            input_genes_Entrez = [x.strip(' ') for x in input_genes_list] # remove any whitespace
            session['genes'] = input_genes_Entrez

        # Assign variables to navbar input selections
        net_type = form.network.data
        features = form.features.data
        GSC = form.negativeclass.data
        CV = form.crossvalidation.data

        tic = time.time()

        # Make a new list that has the IDs converted to ENSG
        # NOTE: This should be moved to the models file
        
        with open(app.config.get('DATA_PATH') + '/ID_conversion/Homo_sapiens_Entrez_to_ENSG_All-Mappings.pickle', 'rb') as handle:
            convert_tmp = pickle.load(handle)

        #with open('./app/data_backend/ID_conversion/Homo_sapiens_Entrez_to_ENSG_All-Mappings.pickle', 'rb') as handle:
        #    convert_tmp = pickle.load(handle)

        input_genes_ENSG = []
        for agene in input_genes_Entrez:
            if agene in convert_tmp:
                input_genes_ENSG = input_genes_ENSG + convert_tmp[agene]

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes_ENSG)

        if request.form['submit_button'] == 'Validate File':
            df_convert_out, table_info = models.make_validation_df(df_convert_out)
            return render_template("validation.html", form=form, table_info=table_info,
                                           validate_table=df_convert_out.to_html(index=False, classes='table table-striped table-bordered" id = "validatetable'))

        elif request.form['submit_button'] == 'Run Model':
            pos_genes_in_net, genes_not_in_net, net_genes = models.get_genes_in_network(convert_IDs,
                                                                                        net_type)  # genes_not_in_net could be an output file
            negative_genes = models.get_negatives(pos_genes_in_net, net_type, GSC)
            mdl_weights, probs, avgps = models.run_SL(pos_genes_in_net, negative_genes, net_genes, net_type, features, CV)
            negative_genes = models.get_negatives(pos_genes_in_net, net_type, GSC)
            df_probs, Entrez_to_Symbol = models.make_prob_df(net_genes, probs, pos_genes_in_net, negative_genes)
            df_GO, df_dis, weights_dict_GO, weights_dict_Dis = models.make_sim_dfs(mdl_weights,GSC,net_type,features) # both of these dfs will be displaed on the webserver
            graph = models.make_small_edgelist(df_probs, net_type, Entrez_to_Symbol)

            tic1 = "{:.2f}".format(time.time()-tic)

            return render_template("results.html", tic1=tic1, form=form, graph=graph,
                                   probs_table=df_probs.to_html(index=False, classes='table table-striped table-bordered" id = "probstable'),
                                   go_table=df_GO.to_html(index=False, classes='table table-striped table-bordered nowrap" style="width: 100%;" id = "gotable'),
                                   dis_table=df_dis.to_html(index=False, classes='table table-striped table-bordered" id = "distable'))



@app.route("/about", methods=['GET'])
def about():

    if request.method == 'GET':

        return render_template("about.html")


@app.route("/results", methods=['GET','POST'])
def results():

    if request.method == 'GET':

        session['genes'] = request.form['genes']

        return render_template("results.html")


@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, "original_exception", None)

    if original is None:
        # direct 500 error, such as abort(500)
        return render_template("/redirects/500.html"), 500

    # wrapped unhandled error
    return render_template("/redirects/500_unhandled.html", e=original), 500
