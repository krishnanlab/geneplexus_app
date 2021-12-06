"""notifier.py : send messages to supplied email
based sendgrid api
"""

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
# by default use config from the application
from app import app

def notify(job_url, job_email, config = app.config):
    """ notify job status by sending email to the address entered in the form"""

    # TODO : decide if we want to use the app config here, or simply send these as params
    # not relying on specific app config keys makes this independently testable

    if not( 'SENDGRID_API_KEY' in config and 'NOTIFIER_EMAIL_ADDRESS' in config ):
        print("email sender is not configured", file=sys.stderr )
        return(None)
    
    # TODO use jinja template 
    message = f"<p>Your job details can be found here: <a href='{job_url}'>{job_url}</a>"

    message = Mail(
        from_email=config['NOTIFIER_EMAIL_ADDRESS'],
        to_emails=job_email,
        subject='Job notification',
        html_content=message)
    try:
        sg = SendGridAPIClient(config['SENDGRID_API_KEY'])
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)

        return(response.status_code)

    except Exception as e:
        print(e.message)
        return(None)

