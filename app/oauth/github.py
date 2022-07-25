from flask import flash
from flask_login import current_user, login_user
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound

from app import db, app
from app.models import User, OAuth

github_blueprint = make_github_blueprint(
    app.config.get('GITHUB_ID'),
    app.config.get('GITHUB_SECRET'),
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
)

@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    if not token:
        flash('Failed to get Github token', 'error')
        return
    resp = blueprint.session.get("/user")
    if not resp.ok:
        flash('Failed to get information from Github', 'error')
        return
    
    github_info = resp.json()

    query = OAuth.query.filter_by(
        provider=github_blueprint.name, provider_user_id=github_info['id']
    )
    if query.first() is not None:
        login_user(query.first().user)
        return
    else:
        if User.query.filter_by(username=github_info['login']).first() is not None:
            flash(f'A user with the Github username {github_info["login"]} already exists')
            return
        user = User(username=github_info["login"], password='', email=github_info['email'], name=github_info['name'])
        oauth = OAuth(
            provider = github_blueprint.name,
            provider_user_id=github_info['id'],
            provider_user_login=str(github_info["login"]),
            token = token,
            user=user,
        )
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash("Successfully signed in with GitHub.")