from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import FileField, SelectField, StringField, TextAreaField, SubmitField

class ModalForm(FlaskForm):
    genes = TextAreaField('genes')
    submit = SubmitField('OK')


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
        ('DisGeNet','DisGeNet'),
        ('GO','GO'),
        ('KEEG','KEEG')
    ]

    job = StringField('job', validators=[DataRequired()])
    genes = FileField('genes', validators=[DataRequired()])
    network = SelectField('network', choices=networks, default=None, validators=[DataRequired()])
    features = SelectField('features', choices=features, default=None, validators=[DataRequired()])
    negativeclass = SelectField('negativeclass', choices=negativeclass, default=None, validators=[DataRequired()])

    runbatch = SubmitField(label='Run batch')
    runlocal = SubmitField(label='Run local')
