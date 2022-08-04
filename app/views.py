from flask.helpers import make_response
from slugify.slugify import slugify
# from mljob.jobs import path_friendly_jobname, launch_job, retrieve_job_folder,retrieve_results,job_info_list,valid_results_filename,results_file_dir,job_exists,retrieve_job_info,generate_job_id, job_status_codes, retrieve_job_outputs
from app import app, db, results_store, job_manager
from mljob.job_manager import generate_job_id


from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for, flash, send_file, Markup, abort,send_from_directory
from flask_login import login_user, logout_user, current_user
from app.forms import ValidateForm, JobLookupForm

from flask_dance.contrib.github import github

from app.models import *
from app.validation_utils import intial_ID_convert, make_validation_df

import os
import numpy as np
import pandas as pd

@app.route("/", methods=['GET'])
@app.route("/index", methods=['GET'])
def index():
    if request.method == 'GET':
        session_args = create_sidenav_kwargs()
        return render_template("index.html", **session_args)

@app.route("/geneset", methods=['GET'])
def geneset():
    if request.method == 'GET':
        session_args = create_sidenav_kwargs()
        return render_template("validation.html", **session_args)


@app.route("/about", methods=['GET'])
def about():
    if request.method == 'GET':
        session_args = create_sidenav_kwargs()
        return render_template("about.html", **session_args)


@app.route("/help", methods=['GET'])
def help():
    if request.method == 'GET':
        session_args = create_sidenav_kwargs()
        return render_template("help.html", **session_args)

@app.route("/contact", methods=['GET'])
def contact():
    session_args = create_sidenav_kwargs()
    return render_template("contact.html", **session_args)


@app.route("/jobs/", methods=['GET', 'POST'])
def jobs():
    """ list jobs in session, show form, or show message from submit"""

    form = JobLookupForm(request.form)
    jobname = form.jobname.data

    if request.method == 'POST' and form.lookup.data:
        if results_store.exists(jobname): #   retrieve_job_folder(jobname, app.config):
            return(redirect(url_for('job',jobname=jobname)))
        else:
            flash(f"Sorry, the job '{jobname}'' was not found")

    jobnames = []
    joblist = {}
    if current_user.is_authenticated:
        jobnames = Job.query.filter_by(userid=current_user.id).with_entities(Job.jobid).all()
        jobnames = [job[0] for job in jobnames]
    if 'jobs' in session:
        jobnames = jobnames + session['jobs']
    
    if len(jobnames) > 0:
        joblist = results_store.job_info_list(jobnames)
        # this now returns a dictionary.  Make it a list for now
        

    session_args = create_sidenav_kwargs()
    return render_template("jobs.html", jobs = jobnames, 
                            joblist = joblist, 
                            form=form, **session_args)
    

@app.route("/jobs/<jobname>", methods=['GET'])
def job(jobname):
    """ show info about job: results if there are some but otherwise basic job information"""
    # sanitize.  if this is an actual jobname this will be idempotent
    jobname = job_manager.cloud_friendly_job_name(jobname)

    #TODO check valid job and 404 if not
    if not results_store.exists(jobname): 
        abort(404)

    job_info = results_store.read_job_info(jobname)
        
    if job_info and job_info['has_results']:
        job_output = results_store.read(jobname)
    else:
        job_output = {}

    return render_template("jobresults.html",
            has_results = job_info['has_results'],
            jobexists = results_store.exists(jobname), 
            jobname=jobname,         
            job_info = job_info,        
            job_output = job_output)

@app.route("/jobs/<jobname>", methods = ["POST"])
def update_job(jobname):
    """ update the job info and possibly notify of new jobs status.  Used by external job runner.  """

    request_data = request.get_json()
    job_status = request_data.get('status')
    
    # sanitize.  if this is an actual jobname this will be idempotent
    jobname = job_manager.cloud_friendly_job_name(jobname)
    # TODO read the data that was posted! to see the event code
    if not results_store.exists(jobname):
        app.logger.info(f"can't notify, job not found {jobname}")
        return {'notifiation response': 404}, 404
    
    job_config = results_store.read_config(jobname)
    job_config['job_url'] =  url_for('job', jobname=jobname ,_external=True)
    
    notifyaddress = job_config.get('notifyaddress')
    if notifyaddress: 
        job_status = results_store.read_status(job_name) 
        if job_status == "completed":
            resp = app.notifier.notify_completed(job_config)
        else:
            resp = app.notifier.notify(notifyaddress, job_config, job_status)

        app.logger.info(f"job status email initiated to {job_config['notifyaddress']} with response {resp}")
        return  {'notification response': resp}, resp
    else:
        return  {'notifiation response': 202}, 202



@app.route("/jobs/<jobname>/results",methods=['GET'])
def jobresults_content(jobname):
    """ this is not longer user, not generating static html results  """
    job_url = url_for('job', jobname=jobname)
    return(f'<html><body><h3 style="padding-top:50px">For results, see <a href="{job_url}">{job_url}</a></h3></body><html>')
    

@app.route("/jobs/<jobname>/results/download/<results_file_name>",methods=['GET'])
def jobresults_download(jobname,results_file_name):
    """get the contents of one of the results outputs and iniate a download.  If no file name or results type is sent
    as a parameter, by default just sent the rendered html.  
    """
    # sanitize the filename using a method for job module
    # results_file_name =  job_manager.cloud_friendly_job_name(results_file_name)
    # if there is any filename left after sanitizing...

    if results_store.results_has_file(jobname, results_file_name):
        # retrieve the file_path, or nothing if the job or file does not exist
        results_directory =  results_store.results_folder(jobname)
        if(results_directory):  
            return send_from_directory(results_directory, results_file_name, as_attachment=True)    
    
    # nothing found, return 404
    abort(404)




@app.route("/results", methods=['GET','POST'])
def results():

    if request.method == 'GET':

        session['genes'] = request.form['genes']

        return render_template("results.html")

@app.route("/cleargenes", methods=['POST'])
def cleargenes():
    session.pop('genes', None)
    session.pop('pos', None)
    session.pop('df_convert_out', None)
    session.pop('table_summary', None)
    session.pop('jobid', None)

@app.route("/validate", methods=['GET','POST'])
def validate():
    form = ValidateForm()

    app.logger.info('validate button')

    string = request.form['genesInput'] # read in the file
    # convert the FileStorage object to a string
    #string = f.stream.read().decode("UTF8")
    # remove any single quotes if they exist
    no_quotes = string.translate(str.maketrans({"'": None}))
    input_genes_list = no_quotes.splitlines()  # turn into a list
    input_genes_list = list(filter(lambda x: x != '', input_genes_list))
    if len(input_genes_list) == 0:
        flash("You need to input at least one positive gene", "error")
        return redirect('index')
    input_genes_upper = np.array([item.upper() for item in input_genes_list])
    # remove any whitespace
    session['genes'] = [x.strip(' ') for x in input_genes_upper]

    input_genes = session['genes']

    # run all the components of the model and pass to the results form
    convert_IDs, df_convert_out = intial_ID_convert(input_genes)

    
    jobid = generate_job_id()
    form.jobid.data = jobid

    df_convert_out, table_summary, input_count = make_validation_df(df_convert_out)
    pos = min([ sub['PositiveGenes'] for sub in table_summary ])

    session['jobid'] = jobid
    session['pos'] = pos
    session['df_convert_out'] = df_convert_out.to_dict()
    session['table_summary'] = table_summary

    return redirect('geneset')


    #return render_template("validation.html", valid_form=form, pos=pos, table_summary=table_summary, existing_genes=input_genes,
    #                        validate_table=df_convert_out.to_html(index=False,
    #                        classes='table table-striped table-bordered" id = "validatetable'))

@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def uploads(filename):
    # Appending app path to upload folder path within app root folder
    uploads = os.path.join(app.root_path, 'static', filename)
    # Returning file from appended path
    return send_file(uploads, as_attachment=True)

@app.route('/get_slugified_text', methods=['POST'])
def get_slugified_text():
    prefix = request.get_json()['prefix']
    clean_text = slugify(prefix.lower())
    return jsonify(success=True, clean_text=clean_text, prefix_too_long=(len(clean_text) > app.config['MAX_PREFIX_LENGTH']), too_long_by=(len(clean_text) - app.config['MAX_PREFIX_LENGTH']))


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
        #session.pop('genes')
        
    else:  # no genes in session
        # if genes are not in the session, 500 server error? read in genes?        
        flash("No geneset seems to be selected - please select a geneset to run the model", "error")
        return redirect('index')
        
    # grab the assigned job ID
    jobid = form.jobid.data

    # Regenerate JobID in the session (not the form)
    # avoid collisions if someone immediately resubmits a job
    session['jobid'] = generate_job_id()

    # if the optional prefix has been added, concatenate
    # the two fields together.  Otherwise the jobname is the jobid
    if form.prefix.data != '':
        friendly_prefix = slugify(form.prefix.data.lower())
        if len(friendly_prefix) > app.config['MAX_PREFIX_LENGTH']:
            friendly_prefix = friendly_prefix[:app.config['MAX_PREFIX_LENGTH']]
        jobname = f'{friendly_prefix}-{jobid}'
    else:
        jobname = jobid

    jobname = job_manager.cloud_friendly_job_name(jobname)

    # this means someone clicked the form to run the batch job. 
    if form.runbatch.data :

        # create dictionary for easy parameter passing
        job_config = {
            'net_type' : form.network.data,
            'features' : form.features.data,
            'GSC': form.negativeclass.data,
            'jobname': jobname,
            'jobid': jobid,
            'job_url': url_for('job', jobname=jobname ,_external=True),
            'notifyaddress': ''  # default is empty string for notification email
        }

        if form.notifyaddress.data != '':   # user has supplied an email address
            # check if the email supplied matched basic pattern
            if form.notifyaddress.validate(form): 
                job_config['notifyaddress']  = form.notifyaddress.data
            else:
                flash("The job notification email address you provided is not a valid email.  No job notification will be sent", category =  "error")

        app.logger.info(f"launching job with job config ={job_config}")
        job_response = job_manager.launch(input_genes, job_config)
        
        #TODO handle unsuccessful responses here 

        app.logger.info(f"job {job_config['jobid']} launched with response {job_response}")

        add_job(jobname)

        job_submit_message = f"Job {jobname} submitted!  The completed job will be available on <a href='{job_config['job_url'] }'>{job_config['job_url']}</a>"

        if job_config.get('notifyaddress'):
            email_response = app.notifier.notify_accepted(job_config)   # notify(job_url, job_email = job_config['notifyaddress'], config = app.config)
            app.logger.info(f"email initiated to {job_config['notifyaddress']} with response {email_response}")
            job_submit_message = job_submit_message + f" and notification sent to {job_config['notifyaddress']}"

        flash(Markup(job_submit_message), category = 'success')

        return redirect('jobs')

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
    session.pop('genes', None)

    file = request.files['formData'].filename
    try:
        string = request.files['formData'].stream.read().decode("UTF8")
        no_quotes = string.translate(str.maketrans({"'": None}))
        input_genes_list = no_quotes.splitlines()  # turn into a list
        input_genes_upper = np.array([item.upper() for item in input_genes_list])
        # remove any whitespace
        toReturn = [x.strip(' ') for x in input_genes_upper]
        return jsonify(success=True, data=toReturn)
    except Exception as e:
        print(e)
        return jsonify(success=False, filename=None)

@app.route('/signup', methods=['POST'])
def signup():
    form_username = request.form.get('username')
    form_email = request.form.get('email')
    form_pass = request.form.get('password')
    form_valid = request.form.get('validpassword')
    form_name = request.form.get('name')
    if User.query.filter_by(username=form_username).first() is not None:
        flash('An account with this username already exists', 'error')
        return redirect('index')
    if form_pass != form_valid:
        flash('Passwords did not match', 'error')
        return redirect('index')
    user = User(form_username, form_pass, form_email, form_name)

    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect('index')

@app.route('/login', methods=['POST'])
def login():
    form_email = request.form.get('email')
    form_pass = request.form.get('password')
    user = User.query.filter_by(email=form_email).first()
    if user is None or not user.verify_password(form_pass):
        # Give user some sort of error
        flash('Username and password combination did not match', 'error')
        return redirect('index')
    login_user(user)
    return redirect('index')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect('index')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    session_args = create_sidenav_kwargs()
    if request.method == 'GET':
        return render_template("edit_profile.html", **session_args)
    form_username = request.form.get('username')
    form_email = request.form.get('email')
    form_name = request.form.get('fullname')
    user = User.query.filter_by(username=form_username).update({'email': form_email, 'name': form_name}, synchronize_session='fetch')
    if user is None:
        # This is a huge problem if this happens. Means that we got to this screen without being logged in
        return redirect('index')
    db.session.commit()
    return redirect('edit_profile')


@app.route('/update_user', methods=['POST'])
def update_user():
    return redirect('index')

@app.route('/github_login', methods=['GET','POST'])
def github_login():
    resp = github.get("/user")
    return redirect('index')


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

def create_sidenav_kwargs():
    if  'genes' in session and \
        'jobid' in session and \
        'pos' in session and \
        'df_convert_out' in session and \
        'table_summary' in session:
        form = ValidateForm()

        form.jobid.data = session['jobid']

        if current_user.is_authenticated and current_user.email:
            form.notifyaddress.data = current_user.email
  
        validate_df = pd.DataFrame(session['df_convert_out'])[['Original ID', 'Entrez ID', 'In BioGRID?', 'In STRING?', 'In STRING-EXP?', 'In GIANT-TN?']]
        validate_html = validate_df.to_html(index=False,
                            classes='table table-striped table-bordered" id = "validatetable')
        return {'existing_genes': session['genes'], 'pos': session['pos'], 
        'table_summary': session['table_summary'], 'validate_table': validate_html, 'valid_form': form,
        'prefix_limit': app.config['MAX_PREFIX_LENGTH']}

    return {}

def add_job(jobname):
    if current_user.is_authenticated:
        userid = current_user.id
        to_add = Job(jobname, userid)
        db.session.add(to_add)
        db.session.commit()
    else:
        if 'jobs' not in session or session['jobs'] is None:
            sessionjobs = []
        else:
            sessionjobs = session['jobs']

        sessionjobs.append(jobname)
        session['jobs'] = sessionjobs