from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for
from app.forms import ValidateForm
from app import app, models
import uuid
import time


@app.route("/", methods=['GET'])
@app.route("/index", methods=['GET'])
def index():

    if request.method == 'GET':

        return render_template("index.html")


@app.route("/jobs", methods=['GET'])
def jobs():

    if request.method == 'GET':

        return render_template("jobs.html")


@app.route("/about", methods=['GET'])
def about():

    if request.method == 'GET':

        return render_template("about.html")

@app.route("/results", methods=['GET','POST'])
def results():

    if request.method == 'GET':

        session['genes'] = request.form['genes']

        return render_template("results.html")


@app.route("/validate", methods=['GET','POST'])
def validate():
    form = ValidateForm()

    if request.method == 'GET':

        return render_template("validation.html")

    elif request.method == 'POST':
        app.logger.info('validate button')
        if 'genes' in session:
            input_genes= session['genes']
        else:
            f = request.files['input_genes'] # read in the file
            string = f.stream.read().decode("UTF8") # convert the FileStorage object to a string
            no_quotes = string.translate(str.maketrans({"'":None})) # remove any single quotes if they exist
            #input_genes_list = no_quotes.split(",") # turn into a list
            input_genes_list = no_quotes.splitlines()  # turn into a list
            input_genes = [x.strip(' ') for x in input_genes_list] # remove any whitespace
            session['genes'] = input_genes


        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes)

        df_convert_out, table_info = models.make_validation_df(df_convert_out)
        return render_template("validation.html", form=form, table_info=table_info,
                               validate_table=df_convert_out.to_html(index=False,
                                                                     classes='table table-striped table-bordered" id = "validatetable'))

@app.route("/run_model", methods=['GET', 'POST'])
def run_model():
    form = ValidateForm()
    if request.method == 'POST':
        # 'genes' exists as a session variable, use that data for subsequent requests
        # if it doesn't, no data has been loaded yet so get the data from a selected file

        if 'genes' in session:
            input_genes = session['genes']

        # Assign variables to navbar input selections
        net_type = form.network.data
        features = form.features.data
        GSC = form.negativeclass.data

        jobname = form.job.data

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes)

        if request.form['submit_button'] == 'Run Model':
            app.logger.info('running model, jobname %s', jobname)

            tic = time.time()
            df_convert_out, table_info = models.make_validation_df(df_convert_out)
            df_convert_out_subset, table_info_subset = models.alter_validation_df(df_convert_out,table_info,net_type)
            graph, df_probs, df_GO, df_dis, avgps = models.run_model(convert_IDs, net_type, GSC, features)
            tic1 = "{:.2f}".format(time.time() - tic)

            app.logger.info('model complete, rendering template')

            # generate html that could be saved to a file for viewing later
            # commented-out for now but will be used for the job-submission system
            # results_html = models.make_template(jobname, net_type, features, GSC, avgps, df_probs, df_GO, df_dis, df_convert_out_subset, table_info_subset, graph)

            session.clear()

            return render_template("results.html", tic1=tic1, form=form, graph=graph, avgps=avgps, table_info=table_info_subset,
                                   probs_table=df_probs.to_html(index=False,
                                                                classes='table table-striped table-bordered" id = "probstable'),
                                   go_table=df_GO.to_html(index=False,
                                                          classes='table table-striped table-bordered nowrap" style="width: 100%;" id = "gotable'),
                                   dis_table=df_dis.to_html(index=False,
                                                            classes='table table-striped table-bordered" id = "distable'),
                                   validate_table = df_convert_out_subset.to_html(index=False,
                                                    classes='table table-striped table-bordered" id = "validatetable')
                                   )


@app.route("/appendhash", methods=['GET','POST'])
def appendhash():

    job = request.form['jobname']
    hash = str(uuid.uuid1())[0:8]
    job_amended = '-'.join([job, hash])

    return jsonify(success=True, jobname=job_amended)


@app.route("/clearinput", methods=['GET','POST'])
def clearinput():

    session.clear()

    return jsonify(success=True)


@app.route("/postgenes", methods=['GET','POST'])
def postgenes():

    session.clear()
    genes = request.form['genes']
    no_quotes = genes.translate(str.maketrans({"'": None}))  # remove any single quotes if they exist
    # input_genes_list = no_quotes.split(",") # turn into a list
    input_genes_list = no_quotes.splitlines()  # turn into a list
    input_genes = [x.strip(' ') for x in input_genes_list]  # remove any whitespace
    session['genes'] = input_genes

    return jsonify(success=True, filename=None)


@app.route("/uploadgenes", methods=['POST'])
def uploadgenes():

    session.clear()
    file = request.files['formData'].filename

    return jsonify(success=True, filename=file)


@app.route("/runbatch", methods=['GET','POST'])
def runbatch():

    if request.method == 'POST':
        # Assign variables to navbar input selections
        net_type = request.form['network']
        features = request.form['feature']
        GSC = request.form['negativeclass']
        jobname = request.form['jobname']

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(session['genes'])

        app.logger.info('running model, jobname %s', jobname)

        tic = time.time()
        df_convert_out, table_info = models.make_validation_df(df_convert_out)
        df_convert_out_subset, table_info_subset = models.alter_validation_df(df_convert_out, table_info, net_type)
        graph, df_probs, df_GO, df_dis, avgps = models.run_model(convert_IDs, net_type, GSC, features)
        tic1 = "{:.2f}".format(time.time() - tic)

        app.logger.info('model complete, rendering template')

        # generate html that could be saved to a file for viewing later
        # commented-out for now but will be used for the job-submission system
        results_html = models.make_template(jobname, net_type, features, GSC, avgps, df_probs, df_GO, df_dis, df_convert_out_subset, table_info_subset, graph)

        session.clear()

        return redirect('jobs')


@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, "original_exception", None)

    if original is None:
        # direct 500 error, such as abort(500)
        return render_template("/redirects/500.html"), 500

    # wrapped unhandled error
    return render_template("/redirects/500_unhandled.html", e=original), 500
