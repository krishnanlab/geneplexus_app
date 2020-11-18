from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import FileField, SelectField, BooleanField
from wtforms.fields.html5 import DecimalRangeField

class IndexForm(FlaskForm):

    networks = [('BioGRID','BioGRID'), ('GIANT','GIANT'), ('STRING','STRING'), ('STRING-EXP','STRING-EXP')]
    features = [('Adjacency','Adjacency'), ('Embedding','Embedding'), ('Influence','Influence')]
    negativeclass = [('DisGeNet','DisGeNet'), ('GO','GO'), ('KEEG','KEEG')]

    genes = FileField('genes', validators=[DataRequired()])
    network = SelectField('network', choices=networks)
    features = SelectField('features', choices=features, default="Embedding")
    negativeclass = SelectField('negativeclass', choices=negativeclass)
    crossvalidation = BooleanField('crossvalidation', default=False)

class AboutForm(FlaskForm):
    pass