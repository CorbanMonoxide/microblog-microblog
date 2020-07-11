from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User


# LOGIN FORM
class LoginForm(FlaskForm): #Inherits FlaskForm
    #Class that creates a login form
    username = StringField('Username', validators = [DataRequired()])
    #Username StringField created to accept UserName
    password = PasswordField('Password', validators = [DataRequired()])
    #password StringField created to accept password
    remember_me =BooleanField('Remember Me')
    #Creates BooleanField (chekbox) to Remember user
    submit = SubmitField('Sign In')
    #SubmitField that allows for sign in


#REGISTRATION FORM
class RegistrationForm(FlaskForm):# Inherits Flask Form
    #Will Create a Registration Form
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a valid email address.')


#EDIT PROFILE FORM
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')


#EMPTY FORM
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


#POST FORM
class PostForm(FlaskForm):
    #Inherits from FlaskForm
    #Class to allow for Submission of Blog Posts
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
        #Creates Text Area. Allows for 140 char posts
    submit = SubmitField('Submit')
        #Creates submit Field


#RESET PASSWORD REQUEST FORM
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

# RESET PASSWORD FORM
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')
