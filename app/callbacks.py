from flask.helpers import make_response
from slugify.slugify import slugify
# from mljob.jobs import path_friendly_jobname, launch_job, retrieve_job_folder,retrieve_results,job_info_list,valid_results_filename,results_file_dir,job_exists,retrieve_job_info,generate_job_id, job_status_codes, retrieve_job_outputs
from app import app, db, results_store, job_manager
from mljob.job_manager import generate_job_id


from werkzeug.exceptions import InternalServerError
from flask import request, render_template, jsonify, session, redirect, url_for, flash, send_file, Markup, abort,send_from_directory, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import ValidateForm, JobLookupForm

from flask_dance.contrib.github import github

from app.models import *
from app.validation_utils import intial_ID_convert, make_validation_df

import os
import numpy as np
import pandas as pd

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

@app.route('/get_slugified_text', methods=['POST'])
def get_slugified_text():
    prefix = request.get_json()['prefix']
    clean_text = slugify(prefix.lower())
    return jsonify(success=True, clean_text=clean_text, prefix_too_long=(len(clean_text) > app.config['MAX_PREFIX_LENGTH']), too_long_by=(len(clean_text) - app.config['MAX_PREFIX_LENGTH']))

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