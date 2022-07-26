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
        provider=github_blueprint.name, provider_user_id=str(github_info['id'])
    )
    if query.first() is not None:
        login_user(query.first().user)
        return False
    else:
        if User.query.filter_by(username=github_info['login']).first() is not None:
            flash(f'A user with the Github username {github_info["login"]} already exists')
            return
        user = User(username=github_info["login"], password='', email=github_info['email'], name=github_info['name'])
        oauth = OAuth(
            provider = github_blueprint.name,
            provider_user_id=str(github_info['id']),
            provider_user_login=str(github_info["login"]),
            token = token,
            user=user,
        )
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash("Successfully signed in with GitHub.")
    # YOU MUST RETURN FALSE. If you do not then Flask-Dance will attempt to create records in the DB as well
    return False

'''
{'login': 'jacobnewsted', 'id': 26586050, 'node_id': 'MDQ6VXNlcjI2NTg2MDUw', 'avatar_url': 'https://avatars.githubusercontent.com/u/26586050?v=4', 'gravatar_id': '', 'url': 'https://api.github.com/users/jacobnewsted', 'html_url': 'https://github.com/jacobnewsted', 'followers_url': 'https://api.github.com/users/jacobnewsted/followers', 'following_url': 'https://api.github.com/users/jacobnewsted/following{/other_user}', 'gists_url': 'https://api.github.com/users/jacobnewsted/gists{/gist_id}', 'starred_url': 'https://api.github.com/users/jacobnewsted/starred{/owner}{/repo}', 'subscriptions_url': 'https://api.github.com/users/jacobnewsted/subscriptions', 'organizations_url': 'https://api.github.com/users/jacobnewsted/orgs', 'repos_url': 'https://api.github.com/users/jacobnewsted/repos', 'events_url': 'https://api.github.com/users/jacobnewsted/events{/privacy}', 'received_events_url': 'https://api.github.com/users/jacobnewsted/received_events', 'type': 'User', 'site_admin': False, 'name': None, 'company': None, 'blog': '', 'location': None, 'email': None, 'hireable': None, 'bio': None, 'twitter_username': None, 'public_repos': 2, 'public_gists': 0, 'followers': 0, 'following': 0, 'created_at': '2017-03-22T00:55:26Z', 'updated_at': '2022-04-05T12:00:08Z'}
'''