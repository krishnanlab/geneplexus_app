from flask.helpers import make_response
from slugify.slugify import slugify
# from mljob.jobs import path_friendly_jobname, launch_job, retrieve_job_folder,retrieve_results,job_info_list,valid_results_filename,results_file_dir,job_exists,retrieve_job_info,generate_job_id, job_status_codes, retrieve_job_outputs
from app import app, db, results_store, job_manager
from mljob.job_manager import generate_job_id
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer


from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for, flash, send_file, Markup, abort,send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from secrets import token_urlsafe
from app.forms import ValidateForm, JobLookupForm

import datetime

from flask_dance.contrib.github import github

from itsdangerous import URLSafeSerializer

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

@app.route('/public_results', methods=['GET'])
def public_results():
    session_args = create_sidenav_kwargs()
    pub_results = Result.query.filter_by(public=True).join(User, Result.userid == User.id)\
                         .add_columns(
                            Result.jobname,
                            User.username,
                            Result.network,
                            Result.feature,
                            Result.negative,
                            Result.p1, Result.p2, Result.p3).all()
    favorites = None
    if current_user.is_authenticated:
        joined_favorites = FavoriteResult.query\
                           .join(Result, FavoriteResult.resultid == Result.id)\
                           .add_columns(Result.id, FavoriteResult.id, Result.jobname)\
                           .filter_by(userid=current_user.id).all()
        
        favorites = [f.jobname for f in joined_favorites]
    return render_template('public_results.html',
                           results=pub_results,
                           favorites = favorites,
                           **session_args)

@login_required
@app.route('/like_result', methods=['POST'])
def like_result():
    data = request.get_json()
    like_status = None
    cur_result = Result.query.filter_by(jobname=data['resultid']).first()
    if cur_result is None:
        return jsonify(f'Result with job name {data["resultid"]} does not exist'), 404
    fav_check = FavoriteResult.query.filter_by(resultid=cur_result.id, userid=current_user.id).first()
    if fav_check is None:
        like_status = True
        print('Adding new favorite for {}'.format(data['resultid']))
        new_fav = FavoriteResult(userid=current_user.id, resultid=cur_result.id)
        db.session.add(new_fav)
        db.session.commit()
    else:
        like_status = False
        print('Deleting new favorite for {}'.format(data['resultid']))
        db.session.delete(fav_check)
        db.session.commit()
    return jsonify({'like_status': like_status}), 200

@app.route('/favorite_results', methods=['GET'])
def favorite_results():
    session_args = create_sidenav_kwargs()
    pub_results = Result.query.filter_by(public=True).all()
    favorites = None
    if not current_user.is_authenticated:
        flash('You cannot access favorites unless you are logged in', 'error')
        return redirect('index')
    favorites = FavoriteResult.query\
                        .join(Result, FavoriteResult.resultid == Result.id)\
                        .join(User, Result.userid == User.id)\
                        .add_columns(Result.jobname, Result.network, Result.feature, Result.negative, Result.p1, Result.p2, Result.p3, User.username)\
                        .filter_by(id=current_user.id).all()
    return render_template('favorite_results.html',
                           results=pub_results,
                           favorites = favorites,
                           **session_args)

@login_required
@app.route('/my_results', methods=['GET'])
def my_results():
    session_args = create_sidenav_kwargs()
    my_results = Result.query.filter_by(userid=current_user.id).all()
    return render_template('my_results.html',
                           results=my_results,
                           **session_args)

def get_results_for_user(resultid, user):
    cur_result = Result.query.filter_by(jobname=resultid).first()
    if cur_result is None:
        return None
    if not cur_result.public:
        if not user.is_authenticated:
            return None
        if cur_result.userid != current_user.id:
            return None
    return cur_result

def is_result_available_to_user(resultid, user):
    cur_result = Result.query.filter_by(jobname=resultid).first()
    if cur_result is None:
        return True
    if not cur_result.public:
        if not user.is_authenticated:
            return False
        if cur_result.userid != current_user.id:
            return False
    return True
    
@app.route('/result/<resultid>', methods=['GET'])
def result(resultid):
    session_args = create_sidenav_kwargs()
    cur_results = get_results_for_user(resultid, current_user)
    if cur_results is None:
        flash(f'Result {resultid} either does not exist or is private', 'error')
        return redirect(url_for('index'))
    else:
        return render_template('result.html',
                            description=cur_results.description,
                            resultid=resultid,
                            author=cur_results.user.username,
                            network=cur_results.network,
                            feature=cur_results.feature,
                            negative=cur_results.negative,
                            performance='{:.2f}, {:.2f}, {:.2f}'.format(cur_results.p1, cur_results.p2, cur_results.p3),
                            public=cur_results.public,
                            **session_args)

@login_required
@app.route('/update_result_visibility', methods=['POST'])
def update_result_visibility():
    data = request.form
    if 'resultid' not in data:
        flash('Result ID was not found in request', 'error')
        return redirect('index')
    cur_result = Result.query.filter_by(jobname=data['resultid']).first()
    if cur_result is None:
        flash('There are no results with ID {}'.format(data['resultid']))
        return redirect(url_for('result', resultid=data['resultid']))
    cur_result.public = not cur_result.public
    db.session.commit()
    return redirect(url_for('result', resultid=data['resultid']))

@login_required
@app.route('/update_result_description', methods=['POST'])
def update_result_description():
    if 'description' not in request.form:
        flash('Could not find a description', 'error')
        return redirect(url_for('result', resultid=request.form['resultid']))
    data = request.form['description']
    cur_result = Result.query.filter_by(jobname=request.form['resultid']).first()
    if cur_result is None:
        flash('Something went wrong when looking up this result', 'error')
        return redirect(url_for('result', resultid=request.form['resultid']))
    cur_result.description = request.form['description']
    db.session.commit()
    return redirect(url_for('job', jobname=request.form['resultid']))


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


    user_jobnames = []
    user_joblist = {}

    session_jobnames = []
    session_joblist = {}

    if current_user.is_authenticated:
        user_jobrecords = Job.query.filter_by(userid=current_user.id).with_entities(Job.jobid).all()
        user_jobnames = [job[0] for job in user_jobrecords]
        user_joblist = results_store.job_info_list(user_jobnames)
    
    if 'jobs' in session:
        session_jobnames = session['jobs']
        if len(session_jobnames) > 0:
            session_joblist = results_store.job_info_list(session_jobnames)  


    session_args = create_sidenav_kwargs()
    return render_template(
        'jobs.html',
        user_jobnames = user_jobnames,
        user_joblist = user_joblist,
        session_jobnames = session_jobnames,
        session_joblist = session_joblist,
        form = form,
        **session_args
    )


def html_output_table(df, id = "", row_limit = 500):
    """ given a data frame, create an html output table for job template for a subset of top rows.
        This assumes the data frame is already in the correct sort order
        
    returns : string of html  or empty string if not a data frame
    """

    #TODO this needs to go away and we need a jinja template macro to build tables instead 
    # this is formattibng code which does not belong in the view or anywhere execpt for a template
    if isinstance(df, pd.DataFrame):        
        html_table = df.head(row_limit).to_html(index=False, classes="table table-striped table-bordered width:100%",table_id = id )
        return(html_table)
    else:
        #TODO log that this is not a dataframe
        return("")
    

@app.route("/jobs/<jobname>", methods=['GET'])
def job(jobname):
    """ show info about job: results if there are some but otherwise basic job information"""
    # sanitize.  if this is an actual jobname this will be idempotent
    jobname = job_manager.cloud_friendly_job_name(jobname)

    #TODO check valid job and 404 if not
    if not results_store.exists(jobname): 
        flash(f'Result "{jobname}" either does not exist or is private', 'error')
        return redirect(url_for('index'))

    job_info = results_store.read_job_info(jobname) # retrieve_job_info(jobname, app.config)

    if job_info and job_info['has_results']:
        job_output = results_store.read(jobname) # retrieve_job_outputs(jobname, app.config)

    else:
        job_output = {}
    
    is_accessible = is_result_available_to_user(jobname, current_user)
    if not is_accessible:
        flash(f'Result "{jobname}" either does not exist or is private', 'error')
        return redirect(url_for('index'))
    
    # TODO simplify this!   don't need jobexists, results_store.read_job_info always returns a dict if job exists
    return render_template("jobresults.html",
            has_results = job_info['has_results'],
            jobexists = results_store.exists(jobname), 
            jobname=jobname,         
            job_info = job_info,   
            job_output = job_output)

##############

@app.route("/jobs/<jobname>", methods = ["POST"])
def _update_job(jobname):
    """ update the job info and possibly notify of new jobs status.  Used by external job runner. 
    if there is a job in the database, create a results file. 
    :param jobname: name of job
    :type jobname: string
     """

    print("callback! ")
    # check job name 
    jobname = job_manager.cloud_friendly_job_name(jobname)
    if not results_store.exists(jobname):
        app.logger.info(f"can't notify, job not found {jobname}")
        return {f'no job found {jobname}': 404}, 404

    # get status from request body. 
    if request.is_json:
        request_data = request.get_json()
    else:
        request_data = request.data()

    print(request_data)    
    job_status =  "Completed" # request_data.get('status')
    job_config = results_store.read_config(jobname)
    notifyaddress = job_config.get('notifyaddress')

    msg = f"job status acknowledged"
    resp = 200
    notifier_resp = ""

    # check if job is complete and has results
    if job_manager.job_completed(jobname):
        app.logger.info(f"job completed {jobname} creating results ")
        ### COMPLETE!   CREATE DB RECORD
        if Result.query.filter_by(jobname=jobname).first() is not None:
            msg = f'Result with JobID {jobname} already has results'
            resp = 405 # method not allowed, can't insert if it exists
            app.logger.info(msg)
        else:
            print(f"looking up job record for {jobname}")
            job_record = Job.query.filter_by(jobid=jobname).first()
            if job_record is not None:   # only create results if there is job record.  If no record, this is not an error condition    
                try:
                    job_info = results_store.read_job_info(jobname) 
                    app.logger.info(f"db: saving job {job_info}")

                    new_result = Result(job = job_record,
                        user = job_record.user,
                        network = job_info.get('net_type'),
                        feature = job_info['features'],
                        negative = job_info['GSC'],
                        p1 = job_info['avgps'][0],
                        p2 = job_info['avgps'][1],
                        p3 = job_info['avgps'][2],
                        public = True
                    )
                    db.session.add(new_result)
                    db.session.commit()
                    app.logger.info(f"db: Results record created for {jobname}")


                except Exception as e:                    
                    msg = f"db: error creating result record for {jobname} : {e}"                
                    resp = 400
                    app.logger.error(msg)
            else:
                app.logger.info(f"db: no job record found, not saving results for {jobname}")
                msg = "no job record to save results for"
                resp = 405

        ### JOB COMPLETE!  Notification
        if notifyaddress:
            notifier_resp = app.notifier.notify_completed(job_config)
            app.logger.info(f"job complete status email initiated to {job_config['notifyaddress']} with response {notifier_resp}")

    else:
        app.logger.info(f"job callback {jobname} but not complete: {job_status}")

        ### incomplete, notify anyway
        if notifyaddress:
            notifier_resp = app.notifier.notify(notifyaddress, job_config, job_status)
            app.logger.info(f"job incomplete status email initiated to {job_config['notifyaddress']} with response {notifier_resp}")
        
    msg = f"{msg};{notifier_resp}"
    return (jsonify({'notification response': msg}), resp)


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

        app.logger.info(f"saving job to db (if logged in)")  
        add_job(jobname) # do this before launching job, because the launcher will trigger saving results, which won't work with out a job record

        app.logger.info(f"launching job with job config ={job_config}")
        job_response = job_manager.launch(input_genes, job_config)        
        #TODO handle unsuccessful responses here 
        app.logger.info(f"job {job_config['jobid']} launched with response {job_response}")
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
    return redirect('edit_profile')

@app.route('/login', methods=['POST'])
def login():
    form_username = request.form.get('username')
    form_pass = request.form.get('password')
    user = User.query.filter_by(username=form_username).first()
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

@app.route('/send_reset', methods=['POST'])
def send_reset():
    form_email = request.form.get('reset_email')
    cur_user = User.query.filter_by(email=form_email).first()
    flash('If the account exists, an email will be mailed with a link to reset shortly', 'success')
    if cur_user is None or cur_user.email is None or cur_user.email == '':
        return redirect(url_for('index'))
    url_string = token_urlsafe(32) # Generate a random token that is url safe
    cur_user.security_token = url_string
    # The token expiration is computed up front based on environment variables
    cur_user.token_expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=app.config['SECURITY_TOKEN_EXPIRATION'])
    # Replace the current lines with email sending
    app.logger.info('Security token for "{}": {}'.format(cur_user.username, cur_user.security_token))
    app.logger.info('Security token expiration: {}'.format(cur_user.token_expiration))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/reset_password/<security_token>', methods=['GET', 'POST'])
def reset_password(security_token):
    user_try = User.query.filter_by(security_token=security_token).first()
    # Check if a user with this security token even exists
    if user_try is None or datetime.datetime.utcnow() > user_try.token_expiration:
        flash('This url does not exist', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST': # If we are posting this form then it means that the user input the new information and are submitting
        password = request.form['password']
        pass_check = request.form['pass_verify']
        if password != pass_check: # Check if the two provided passwords are the same
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', security_token=security_token)
        user_try.update_password(password)
        user_try.security_token = None # Make sure the same security token cannot be used again
        user_try.token_expiration = None
        db.session.commit()
        flash('Successfully updated password', 'success')
        return redirect(url_for('index'))
    return render_template('reset_password.html', security_token=security_token, username=user_try.username)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    session_args = create_sidenav_kwargs()
    if request.method == 'GET':
        return render_template("edit_profile.html", **session_args)
    form_username = request.form.get('username')
    form_email = request.form.get('email')
    form_name = request.form.get('fullname')
    if current_user.username != form_username:
        # This is a big no-no. We cannot have a user in the edit profile screen without a matching username (this could be because of a malicious user)
        flash('Something went terribly wrong, please try again', 'error')
        return redirect(url_for('index'))
    user = User.query.filter_by(username=form_username).first()
    if user is None:
        # This would entail some other kinda bad state, this time a DB error of some sort
        flash('Something went terribly wrong, please try again', 'error')
        return redirect(url_for('index'))
    email_test = User.query.filter_by(email=form_email).first()
    if email_test is not None and email_test.username != user.username:
        flash('Another user with this email already exists, please try another', 'error')
        return redirect('edit_profile')
    user.email = form_email
    user.name = form_name
    db.session.commit()
    flash('Successfully updated account', 'success')
    return redirect(url_for('edit_profile'))


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
        user_id = current_user.id
        to_add = Job(jobid=jobname, userid=user_id)
        db.session.add(to_add)
        db.session.commit()
    else:
        if 'jobs' not in session or session['jobs'] is None:
            sessionjobs = []
        else:
            sessionjobs = session['jobs']

        sessionjobs.append(jobname)
        session['jobs'] = sessionjobs

def get_or_set_job(jobname):
    results = None
    # First we need to check the DB if the job already exists
    result_check = Result.query.filter_by(jobname=jobname).first()
    if result_check is not None:
        print()
        # If this isn't none then the result already existed within the database, just return that
        return result_check
    
    job_info = results_store.read_job_info(jobname) #  retrieve_job_info(jobname, app.config)
    job_output = {}

    if job_info and job_info['has_results']:
        job_output = results_store.read(jobname)
        # If we didn't get it back then we need to check if the job even exists in the jobs table
        result_check = Job.query.filter_by(jobid=jobname).first()
        if result_check is not None:
            # The job exists, we just don't have a result made yet
            to_add = Result(
                network = job_info['net_type'],
                feature = job_info['features'],
                negative = job_info['GSC'],
                p1 = job_output['avgps'][0],
                p2 = job_output['avgps'][1],
                p3 = job_output['avgps'][2],
                user = result_check.user,
            )
            db.session.add(to_add)
            db.session.commit()
    return job_info, job_output

@login_required
@app.route('/update_result', methods=['POST'])
def update_result():
    data = request.get_json()
    result_check = Result.query.filter_by(jobname=data['jobname']).first()
    if result_check is not None:
        return jsonify(f'Result with JobID {data["jobname"]} already has results'), 400
    result_check = Job.query.filter_by(jobid=data['jobname']).first()
    if result_check is None:
        return jsonify(f'Job with JobID {data["jobname"]} does not exists'), 400
    try:
        new_result = Result(
            job = result_check,
            user = result_check.user,
            network = data['network'],
            feature = data['feature'],
            negative = data['negative'],
            p1 = data['avgps'][0],
            p2 = data['avgps'][1],
            p3 = data['avgps'][2],
            public = True,
        )
        print('New result')
        print(new_result)
        db.session.add(new_result)
        db.session.commit()
        return jsonify(f'Job with JobID {data["jobname"]} has results created'), 200
    except Exception as e:
        return jsonify(str(e)), 400
