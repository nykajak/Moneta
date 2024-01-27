from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField
from wtforms.validators import DataRequired,Length,Email,EqualTo

class MyRegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=5,max=20)])
    email = StringField('Email',validators=[DataRequired(),Email(message="Please provide valid email!")])
    password = PasswordField('Password',validators=[DataRequired(),Length(min = 6,max=60)])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),Length(min = 6,max=60),EqualTo('password',message="Password and confirm password should match!")])
    submit = SubmitField('Sign Up')

class MyLoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email(message="Please provide valid email!")])
    password = PasswordField('Password',validators=[DataRequired(),Length(min = 6,max=60)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')