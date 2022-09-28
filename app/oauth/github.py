import os

from flask import flash, url_for, request
from flask_login import current_user, login_user
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound

from app.db import db
from app.models import User, OAuth

# This is the blueprint that will registered with the app when the app is initialized
github_blueprint = make_github_blueprint(
    os.getenv('GITHUB_ID'),
    os.getenv('GITHUB_SECRET'),
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
)

# A wrapper function for the SSO callback
# PLEASE NOTE, all return paths MUST return False or else Flask-Dance will try to do it's own functionality (which causes errors)
@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    if not token:
        # This could fail for a couple of reasons, one of which is that the request didn't have the correct ID and/or secret
        flash('Failed to get Github token', 'error')
        return False
    resp = blueprint.session.get("/user")
    if not resp.ok:
        # The only reason this would fail is if the SSO page owned by Github failed. This won't be an issue most likely
        flash('Failed to get information from Github', 'error')
        return False
    
    github_info = resp.json()

    # We need to check if the the OAuth token for that given provider (Github) exists with the given user's ID
    query = OAuth.query.filter_by(
        provider=github_blueprint.name, provider_user_id=str(github_info['id'])
    )
    if query.first() is not None:
        # If it exists we just log the user in (based on the linked User object in the DB)
        login_user(query.first().user)
        return False
    else:
        if User.query.filter_by(username=github_info['login']).first() is not None:
            # This could happen for one of two reasons:
            # 1 - There already exists an account with that username
            #   + I create an account on the website with name JohnDoe, then try to register my Github account to the site
            #     which also has the username JohnDoe, it detects 2 JohnDoe's and this happens
            # 2 - Something really sinister has happneed and somehow a User was created but an OAuth was not, this would be a
            #     HUGE problem and would need to be looked into since it would mean there could be many of these issues
            flash(f'A user with the Github username {github_info["login"]} already exists')
            return
        # Create a new user
        user = User(username=github_info["login"], password='', email=github_info['email'], name=github_info['name'])
        # Create an OAuth token to link to that user
        oauth = OAuth(
            provider = github_blueprint.name,
            provider_user_id=str(github_info['id']),
            provider_user_login=str(github_info["login"]),
            token = token,
            user=user,
        )

        # Commit, then login
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash('Successfully signed in with GitHub.', 'success')
        if github_info['email'] is None or github_info['email'] == '':
            # This needs to be updated with a much better message. I wanted to get the URL for edit_profile but I cannot get the base URL since request.base_url returns the API redirect URL (which includes the github part of the URL)
            flash('Your Github account did not provide an email. If you would like to edit your profile and add an email in edit_profile', 'error')
    # YOU MUST RETURN FALSE. If you do not then Flask-Dance will attempt to create records in the DB as well
    return False