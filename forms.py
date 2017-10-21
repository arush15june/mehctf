from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class RegisterForm(Form):
    username = StringField('Username',
                            validators=[DataRequired()])
    password = PasswordField('Password',
                            validators=[DataRequired()])
    submit = SubmitField('Submit')
