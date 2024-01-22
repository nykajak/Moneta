from flask_security import RegisterForm,LoginForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField
from wtforms.validators import DataRequired,Length,Email,EqualTo

class MyRegistrationForm(RegisterForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=5,max=20)])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min = 6,max=60)])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),Length(min = 6,max=60),EqualTo('password')])
    submit = SubmitField('Sign Up')

class MyLoginForm(LoginForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(),Length(min = 6,max=60)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

    def validate(self, **kwargs):
        return super().validate(**kwargs)