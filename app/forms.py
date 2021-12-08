from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms import FileField, SelectField, StringField, TextAreaField, SubmitField


class ModalForm(FlaskForm):
    genes = TextAreaField('genes')
    submit = SubmitField('OK')


class JobLookupForm(FlaskForm):
    jobname = StringField('job', validators=[DataRequired()])
    lookup = SubmitField(label='Lookup job')


# form to submit a job from the page validation.html
class ValidateForm(FlaskForm):
    networks = [
        ('BioGRID','BioGRID'),
        ('GIANT-TN','GIANT-TN'),
        ('STRING','STRING'),
        ('STRING-EXP','STRING-EXP')
    ]
    features = [
        ('Adjacency','Adjacency'),
        ('Embedding','Embedding'),
        ('Influence','Influence')
    ]

    negativeclass = [
        ('DisGeNet','Diseases (DisGeNet)'),
        ('GO','Processes / pathways (GO)')
    ]

    job = StringField('job', validators=[DataRequired()], render_kw={'readonly': True})
    prefix = StringField('prefix')
    genes = FileField('genes', validators=[DataRequired()])
    network = SelectField('network', choices=networks, default=None, validators=[DataRequired()])
    features = SelectField('features', choices=features, default=None, validators=[DataRequired()])
    negativeclass = SelectField('negativeclass', choices=negativeclass, default=None, validators=[DataRequired()])
    notifyaddress = StringField('notifyaddress',validators=[Email()])

    runbatch = SubmitField(label='Submit')

