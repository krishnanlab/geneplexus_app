from app.jobs import path_friendly_jobname, launch_job, list_all_jobs, retrieve_job_folder,check_results, retrieve_results, retrieve_job_info,job_info_list

from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for, flash
from app.forms import ValidateForm, JobLookupForm
from app import app, models
import uuid
import time
import os


@app.route("/", methods=['GET'])
@app.route("/index", methods=['GET'])
def index():

    if request.method == 'GET':

        return render_template("index.html")


@app.route("/about", methods=['GET'])
def about():

    if request.method == 'GET':

        return render_template("about.html")


@app.route("/help", methods=['GET'])
def help():

    if request.method == 'GET':

        return render_template("help.html")


@app.route("/jobs/", methods=['GET', 'POST'])
def jobs():
    """ list jobs in session, show form, or show message from submit"""

    form = JobLookupForm(request.form)
    jobname = form.jobname.data

    if request.method == 'POST' and form.lookup.data:
            if retrieve_job_folder(jobname, app.config):
                return(redirect(url_for('job',jobname=jobname)))
            else:
                flash(f"Sorry, the job '{jobname}'' was not found")

    jobnames = list_all_jobs(app.config.get('JOB_PATH'))
    joblist = job_info_list(jobnames, app.config)

    return render_template("jobs.html", jobs = jobnames, 
                            joblist = joblist, 
                            form=form)


@app.route("/jobs/<jobname>", methods=['GET'])
def job(jobname):
    """ """
    return render_template("jobresults.html", jobname = jobname)


@app.route("/jobs/<jobname>/results")
def jobresults_content(jobname):
    """ read the results into memory and return """
    results_content = retrieve_results(jobname, app.config)
    if results_content:
        return(results_content) # or in future, send this html to a template wrapper        
    else:
        return(f'<html><body><div class="container"><h3 style="padding-top:50px"> No results yet for the job "{jobname}"</h3></div></body><html>')


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
        if not 'genes' in session:
            f = request.files['input_genes'] # read in the file
            # convert the FileStorage object to a string
            string = f.stream.read().decode("UTF8")
            # remove any single quotes if they exist
            no_quotes = string.translate(str.maketrans({"'": None}))
            #input_genes_list = no_quotes.split(",") # turn into a list
            input_genes_list = no_quotes.splitlines()  # turn into a list
            # remove any whitespace
            session['genes'] = [x.strip(' ') for x in input_genes_list]

        input_genes = session['genes']

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes)

        # assign a job name
        jobname = str(uuid.uuid1())[0:8]

        df_convert_out, table_summary, input_count = models.make_validation_df(df_convert_out)
        return render_template("validation.html", form=form, table_summary=table_summary,jobname=jobname,
                               validate_table=df_convert_out.to_html(index=False,
                               classes='table table-striped table-bordered" id = "validatetable'))


@app.route("/run_model", methods=['POST'])
def run_model():
    """post-only route to run model locally or trigger cloud, depending on button """
    form = ValidateForm()
    # 'genes' exists as a session variable, use that data for subsequent requests
    # if it doesn't, no data has been loaded yet so get the data from a selected file
    if 'genes' in session:
        input_genes = session['genes']

    # if genes are not in the session, 500 server error? read in genes?
    # else:
    #    f = request.files['input_genes']  # read in the file
    #    input_genes = models.read_input_file(f)

    
    # Assign variables to navbar input selections
    net_type = form.network.data
    features = form.features.data
    GSC = form.negativeclass.data

    jobname = form.job.data

    if form.runbatch.data :

        # create dictionary for easy parameter passing
        job_config = {}
        job_config['net_type'] = net_type
        job_config['features'] = features
        job_config['GSC'] = GSC
        job_config['jobname'] = jobname

        print("launching job with job config =")
        print(job_config)

        response = launch_job(session['genes'], job_config, app.config)
        print("response = ", response)

        session.clear()

        flash(f"Job {jobname} submitted!  The completed job will be available on {url_for('job', jobname=jobname)}")

        return redirect('jobs')

    if form.runlocal.data : 

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes)


        # this runs the model on the spot
        # note we should also create job folder, and save results there, too
        app.logger.info('running model, jobname %s', jobname)

        tic = time.time()
        df_convert_out, table_summary, input_count = models.make_validation_df(df_convert_out)
        df_convert_out_subset, positive_genes = models.alter_validation_df(df_convert_out,table_summary,net_type)
        graph, df_probs, df_GO, df_dis, avgps = models.run_model(convert_IDs, net_type, GSC, features)
        tic1 = "{:.2f}".format(time.time() - tic)

        app.logger.info('model complete, rendering template')

        # generate html that could be saved to a file for viewing later
        # commented-out for now but will be used for the job-submission system
        # TODO save these results as a file just like 
        # results_html = models.make_template(jobname, net_type, features, GSC, avgps, df_probs, df_GO, df_dis, df_convert_out_subset, table_info_subset, graph)

        session.clear()

        return render_template("results.html", tic1=tic1, form=form, graph=graph, avgps=avgps, input_count=input_count,
                                positive_genes=positive_genes,
                                probs_table=df_probs.to_html(index=False,
                                                            classes='table table-striped table-bordered" id = "probstable'),
                                go_table=df_GO.to_html(index=False,
                                                        classes='table table-striped table-bordered nowrap" style="width: 100%;" id = "gotable'),
                                dis_table=df_dis.to_html(index=False,
                                                        classes='table table-striped table-bordered" id = "distable'),
                                validate_table = df_convert_out_subset.to_html(index=False,
                                                classes='table table-striped table-bordered" id = "validatetable')
                                )
    # submit button value is neither possibility
    return("invalid form data ")

@app.route("/appendprefix", methods=['GET','POST'])
def appendPrefix():

    job = request.form['jobname']
    prefix = request.form['prefix']
    job_amended = '-'.join([prefix, job])

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



@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, "original_exception", None)

    if original is None:
        # direct 500 error, such as abort(500)
        return render_template("/redirects/500.html"), 500

    # wrapped unhandled error
    return render_template("/redirects/500_unhandled.html", e=original), 500
