from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf.recaptcha import RecaptchaField
from wtforms.validators import DataRequired

# Recaptcha Keys

RECAPTCHA_PUBLIC_KEY = '6LcItjUUAAAAAIJnAqsuH3FOJm6mI5Y--ei7JXgl'
RECAPTCHA_PRIVATE_KEY = '6LcItjUUAAAAAHBxk9C_QR6RLn4-49MNPoRDQuOG'

class RegisterForm(FlaskForm):
    username = StringField('Username',
                            validators=[DataRequired()])
    password = PasswordField('Password',
                            validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField('Submit')

class ChangePasswordForm(FlaskForm):
    oldpassword = PasswordField('Current Password',
                            validators=[DataRequired()])
    newpassword = PasswordField('New Password',
                            validators=[DataRequired()])
    newpasswordretype = PasswordField('Retype New Password',
                            validators=[DataRequired()])