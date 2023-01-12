from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Special Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

    def validate_email(self, email):
        email = email.data
        if not (email.endswith('@gmail.com') or email.endswith('@ukr.net')):
            raise ValidationError('Email must end with @gmail.com or @ukr.net')


