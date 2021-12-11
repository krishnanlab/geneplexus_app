"""notifier.py : send messages to supplied email
based sendgrid api
"""

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import sys, os.path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Environment, FileSystemLoader


class Notifier():
    """Send Notification emails based on job events using standard templates defined in a template folder
    Uses sendgrid and requires configuration values in an an app dictionary
    
    example usage: (if templates are in the templates folder)
        job_config = launch a job...
        notifier = Notifier(app.config,  job_status_codes)
        notifier_response = notifier.notify_create(job_config['notifyaddress'], job_config)
        if notifier_response:
            flash(f"{job_config['notifyaddress']} notified of job creation")
        else:
            flash(f"error, email notification could not be sent")
        

        job_config = job_completed(jobname)
        notifier = Notifier(app.config, job_status_code)
        notifier_response = notifier.notify_completed(job_config['notifyaddress'], job_config)

        # or initialize when creating the app and use that

        from jobs import job_status_codes # or whatever
        from app.notifier import Notifier
        app.notifier = Notifier(app.config, job_status_codes)
        
        # then in view

        job_config = launch_job(request.form)
        notification_feedback = app.notifier.notify_create(job_config)
        flash(notification_feedback)

    """

    def __init__(self, app_config, job_status_codes = {202:"Accepted", 200:"Completed"},template_folder = 'templates'):

        if 'SENDGRID_API_KEY' not in app_config:
            print("The 'SENDGRID_API_KEY' was not found in application configuration", file = sys.stderr)
            return(None)
        
        self.api_key = app_config.get('SENDGRID_API_KEY')
        self.sender_email = app_config.get('NOTIFIER_EMAIL_ADDRESS')
        self.app_config = app_config # What else do we really need from app_config??
        self.job_status_codes = job_status_codes
        module_root = os.path.join(os.path.dirname(__file__), template_folder)
        self.template_env = Environment(loader=FileSystemLoader(module_root))

    def render_message(self, job_config, event=None):
        """ using standard job status codes, find template file and build jinja template"""
        # TODO perhaps this should have a generic HTML message in case the templates are not found?
        # job status codes is int keyed dict of string codes 200:created. 
        if event in self.job_status_codes:
            event_str = self.job_status_codes[event].lower()

        elif event.lower() in self.job_status_codes.values():
            event_str = event.lower()
        else:
            event_str = 'base'

        message_content = None
        # standard template file name use the event code (create, completed, etc)
        # TODO put some basic information in the base template that can be overridden

        template_file = f"notification_job_{event_str}.html"

        try:
            template = self.template_env.get_template(template_file )
            message_content = template.render(job_config = job_config, app_config = self.app_config)
        except Exception as e:
            print("Template not found or couldn't render", template_file, e, file = sys.stderr)
        
        return(message_content)

    def send_email(self, to_address, message_content, subject_line):
        """ send an email using sendgrid with given address, content and subject line"""
        if 'SENDGRID_API_KEY' not in self.app_config:
            print("The 'SENDGRID_API_KEY' was not found in application configuration", file = sys.stderr)
            return(None)

        message = Mail(from_email=self.sender_email,
                to_emails=to_address,
                subject=subject_line,
                html_content=message_content)

        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            print(response.status_code, file=sys.stderr)
            print(response.body,file=sys.stderr)
            print(response.headers,file=sys.stderr)

            return(response.status_code)

        except Exception as e:
            print("notification mailer error", e, file=sys.stderr)
            return(None)

    def notify(self, to_address, job_config, event, subject_line = "Geneplexus: job information"):
        """create and deliver a message based on standard job status codes"""
        message_content = self.render_message(job_config, event)
        mail_status_code = self.send_email(to_address, message_content, subject_line)
        return(mail_status_code)
            
    def notify_create(self, job_config):
        """ standard create job notification"""
        if ('jobname' in job_config )and ('notifyaddress' in job_config):
            return(self.notify(job_config['notifyaddress'], job_config, 202, subject_line = f"Geneplexus: job '{job_config['jobname'] }' created"))
        else:
            print('job info missing notifyaddress and.or jobname', file=sys.stderr)
            return(None)

    def notify_completed(self, to_address, job_config):
        """ standard job completed message"""
        if ('jobname' in job_config) and ('notifyaddress' in job_config):
            return(self.notify(job_config['notifyaddress'], job_config, 202, subject_line = f"Geneplexus: job '{job_config['jobname']}' completed"))
        else:
            print('job info missing notifyaddress and.or jobname', file=sys.stderr)
            return(None)


def test_notifier(app, address='mail@billspat.com'):
    """ send test message, requires an app object (e.g. run from Flask shell ) """
        
    ex_job_config = {'net_type' : 'BioGRID', 'features':'Embedding','GSC':'GO','jobname':"example_job_12345",'notifyaddress':address}
    notifier = Notifier(app.config)
    notifier_response = notifier.notify_create(ex_job_config)
    if notifier_response:
        print(notifier_response)
    else:
        print(" notifier did not respond")






# previous vesion
# todo - delete this once tested
def notify(job_url, job_email, app_config):
    """ notify job status by sending email to the address entered in the form"""

    # TODO : decide if we want to use the app config here, or simply send these as params
    # not relying on specific app config keys makes this independently testable

    if not( 'SENDGRID_API_KEY' in config and 'NOTIFIER_EMAIL_ADDRESS' in config ):
        print("email sender is not configured", file=sys.stderr )
        return(None)
    
    # TODO use jinja template 
    message_content = f"<p>Your job details can be found here: <a href='{job_url}'>{job_url}</a>"
    subject_line = "Geneplexus: job submitted"
    response = send_notification(job_email, subject_line, message_content, app_config)
    return(response)

def send_notification(job_email, subject_line, message_content, app_config):

    message = Mail(
        from_email=app_config['NOTIFIER_EMAIL_ADDRESS'],
        to_emails=job_email,
        subject=subject_line,
        html_content=message_content)

    try:
        sg = SendGridAPIClient(config['SENDGRID_API_KEY'])
        response = sg.send(message)
        print(response.status_code, file=sys.stderr)
        print(response.body,file=sys.stderr)
        print(response.headers,file=sys.stderr)

        return(response.status_code)

    except Exception as e:
        print("notification mailer error", e, file=sys.stderr)
        return(None)

