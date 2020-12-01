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
        '''
        input_genes_Entrez = ['6457', '7037', '57403', '3134', '50807', '93343', '11311', '8766', '5584', '137492',
                              '998',
                              '30011', '5337', '3312', '155', '10015', '55738', '57132', '153', '116986', '163',
                              '11267',
                              '1950', '3559', '6714', '84249', '2066', '29924', '1213', '30846', '84612', '440073',
                              '2060',
                              '3303', '3561', '9101', '51160', '56904', '3304', '23527', '5878', '3560', '7189', '3949',
                              '92421', '26286', '5979', '9922', '11031', '116983', '2261', '9230', '5867', '64145',
                              '867', '57154', '84313', '3577', '116987', '10617', '1436', '200576', '83737', '23396',
                              '3310', '5590', '3133', '382', '6456',
                              '30845', '868', '2264', '5868', '84440', '116984', '5869', '23624', '22841', '161',
                              '23096', '5338', '652614', '84552', '51028', '55616', '9829', '3815', '29082', '9135',
                              '23362', '9146', '128866', '156',
                              '8218', '89853', '154', '64744', '9525', '84364', '9727', '23550', '8853', '1956', '8395',
                              '6455', '64411',
                              '5156', '51100', '8027', '408', '3305', '51534', '2868', '9744', '3106', '51652', '3265',
                              '27243', '10938',
                              '60682', '157', '26056', '10059', '2321', '80230', '1173', '1175', '160', '3306', '3135',
                              '1234', '2149',
                              '8411', '3791', '51510', '23327', '409', '11059', '3579', '27183', '8396', '1601', '1211',
                              '3480',
                              '9815', '26119', '64750', '26052', '4914', '25978', '8394', '1212', '30844', '131890',
                              '79720',
                              '7251', '50855', '116985', '5662', '2870', '10193', '1785', '155382', '652799', '22905',
                              '3105',
                              '55048', '10254', '55040', '7852', '1759', '4193', '2869', '2065', '6011', '4734',
                              '28964',
                              '4233', '80223', '79643', '3107', '2263', '56288']
        '''
        # 'genes' exists as a session variable, use that data for subsequent requests
        # if it doesn't, no data has been loaded yet so get the data from a selected file
        if 'genes' in session:
            input_genes_Entrez = session['genes']
        else:
            genes = request.files.get('input_genes')
            genes_list = genes.read().decode("utf-8").splitlines()
            input_genes_Entrez = genes_list[0]
            session['genes'] = input_genes_Entrez

        # Assign variables to navbar input selections
        net_type = form.network.data
        features = form.features.data
        GSC = form.negativeclass.data
        CV = form.crossvalidation.data

        tic = time.time()

        # Make a new list that has the IDs converted to ENSG
        # NOTE: This should be moved to the models file
        with open(app.config['DATA_PATH'] + "/ID_conversion/Homo_sapiens_Entrez_to_ENSG_All-Mappings.pickle", 'rb') as handle:
            convert_tmp = pickle.load(handle)
        input_genes_ENSG = []
        for agene in input_genes_Entrez:
            if agene in convert_tmp:
                input_genes_ENSG = input_genes_ENSG + convert_tmp[agene]

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes_ENSG)
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
                               convert_table=df_convert_out.to_html(index=False, classes='table table-striped table-bordered" id = "converttable'),
                               probs_table=df_probs.to_html(index=False, classes='table table-striped table-bordered" id = "probstable'),
                               go_table=df_GO.to_html(index=False, classes='table table-striped table-bordered" id = "gotable'),
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
