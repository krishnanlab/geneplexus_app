from app.jobs import path_friendly_jobname, launch_job, list_all_jobs, retrieve_job_folder,check_results, retrieve_results, retrieve_job_info,job_info_list

from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for, flash, send_file, Markup
from app.forms import ValidateForm, JobLookupForm
from app import app, models
from app.notifier import notify

import os
import uuid
import numpy as np



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

@app.route("/contact", methods=['GET'])
def contact():
    return render_template("contact.html")


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

    if 'jobs' in session and session['jobs']:
        jobnames = session['jobs']
        # jobnames = list_all_jobs(app.config.get('JOB_PATH'))
        joblist = job_info_list(jobnames, app.config)
    else:
        jobnames = []
        joblist = {}

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
            input_genes_list = no_quotes.splitlines()  # turn into a list
            input_genes_upper = np.array([item.upper() for item in input_genes_list])
            # remove any whitespace
            session['genes'] = [x.strip(' ') for x in input_genes_upper]

        input_genes = session['genes']

        # run all the components of the model and pass to the results form
        convert_IDs, df_convert_out = models.intial_ID_convert(input_genes)

        df_convert_out, table_summary, input_count = models.make_validation_df(df_convert_out)
        pos = min([ sub['PositiveGenes'] for sub in table_summary ])
        return render_template("validation.html", form=form, pos=pos, table_summary=table_summary,
                               validate_table=df_convert_out.to_html(index=False,
                               classes='table table-striped table-bordered" id = "validatetable'))

@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def uploads(filename):
    # Appending app path to upload folder path within app root folder
    uploads = os.path.join(app.root_path, 'static', filename)
    # Returning file from appended path
    return send_file(uploads, as_attachment=True)


@app.route("/run_model", methods=['POST'])
def run_model():
    """post-only route to run model locally or trigger cloud, depending on button """
    form = ValidateForm()
    # 'genes' exists as a session variable, use that data for subsequent requests
    # if it doesn't, no data has been loaded yet so get the data from a selected file
    if 'genes' in session:
        # save session data to variable
        input_genes = session['genes']
        # remove the current genelist from session
        # why remove the geneset from session -- what if someone wants to run a second job with same geneset?
        session.pop('genes')
        
    else:  # no genes in session
        # if genes are not in the session, 500 server error? read in genes?        
        flash("No geneset seems to be selected - please select a geneset to run the model")
        return redirect('index')

    #    f = request.files['input_genes']  # read in the file
    #    input_genes = models.read_input_file(f)

    # assign a job id
    jobid = str(uuid.uuid1())[0:8]

    # if the optional prefix has been added, concatenate
    # the two fields together.  Otherwise the jobname is the jobid
    if form.prefix.data != '':
        jobname = f'{form.prefix.data}-{jobid}'
    else:
        jobname = jobid

    jobname = path_friendly_jobname(jobname)

    # this means someone clicked the form to run the batch job. 
    if form.runbatch.data :

        # create dictionary for easy parameter passing
        job_config = {}
        job_config['net_type'] = form.network.data
        job_config['features'] = form.features.data
        job_config['GSC'] = form.negativeclass.data
        job_config['jobname'] = jobname
        job_config['jobid'] = jobid
        job_config['notifyaddress'] = ''  # default is empty string for notification email

        if form.notifyaddress.data != '':   # user has supplied an email address
           job_config['notifyaddress'] = form.notifyaddress.data

        print("launching job with job config =")
        print(job_config)

        job_response = launch_job(input_genes, job_config, app.config)
        app.logger.info(f"job {job_config['jobid']} launched with response {job_response}")

        job_url = url_for('job', jobname=jobname ,_external=True)

        #TODO change email message depending on job launch response
        if 'notifyaddress' in job_config:
            email_response = notify(job_url, job_email = job_config['notifyaddress'], config = app.config)
            app.logger.info(f"email initiated to {job_config['notifyaddress']} with response {email_response}")

        if 'jobs' in session and session['jobs']:
            session['jobs'] = session['jobs'].append(jobname)
        else:
            session['jobs'] = [jobname]

        job_submit_message = f"Job {jobname} submitted!  The completed job will be available on <a href='{job_url}'>{job_url}</a>"
    
        if job_config['notifyaddress']:
            job_submit_message = job_submit_message + " and notification sent to {job_config['notifyaddress']}"

        flash(Markup(job_submit_message))

        return redirect('jobs')

    # this option is for testing, and not usually available as a button on the website
    if form.runlocal.data : 
        # this runs the model on the spot and simply returns the results as HTML file
        app.logger.info('running model, jobname %s', jobname)
        results_html = models.run_and_render(input_genes, net_type, features, GSC, jobname)
        app.logger.info('model complete, rendering template')
        return(results_html)

    # we reach here if the submit button value is neither possibility
    return("invalid form data ")


@app.route("/clearinput", methods=['GET','POST'])
def clearinput():
    try:
        session.pop('genes')
    except KeyError:
        pass

    return jsonify(success=True)


@app.route("/postgenes", methods=['GET','POST'])
def postgenes():

    try:
        session.pop('genes')
    except KeyError:
        pass


    genes = request.form['genes']
    no_quotes = genes.translate(str.maketrans({"'": None}))  # remove any single quotes if they exist
    # input_genes_list = no_quotes.split(",") # turn into a list
    input_genes_list = no_quotes.splitlines()  # turn into a list
    input_genes_upper = np.array([item.upper() for item in input_genes_list])
    session['genes'] = [x.strip(' ') for x in input_genes_upper] # remove any whitespace

    return jsonify(success=True, filename=None)


@app.route("/uploadgenes", methods=['POST'])
def uploadgenes():

    # remove genes from session
    try:
        session.pop('genes')
    except KeyError:
        pass

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

@app.context_processor
def inject_template_scope():
    injections = dict()
    def cookies_check():
        value = request.cookies.get('cookie_consent')
        return value == 'true'
    injections.update(cookies_check=cookies_check)
    return injections