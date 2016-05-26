from wtforms import Form
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(Form):
    query = StringField('query', validators=[DataRequired()])
    search_button = SubmitField('Search for!')
