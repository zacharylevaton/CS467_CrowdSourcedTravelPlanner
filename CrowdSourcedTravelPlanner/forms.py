from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from CrowdSourcedTravelPlanner.models import User
from flask_login import current_user
from flask_wtf.file import FileField, FileAllowed


class RegistrationForm(FlaskForm):
    """
    Defines the Flask form elements for the "Registration" page.  Input validation methods include specifying required
    form fields, checking password length, checking for valid email address structure, and making sure the "Confirm
    Password" field matches the entered password.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        """Checks if the username already exists in the database."""

        # Query the database to see if the given username is already present
        user = User.query.filter_by(username=username.data).first()

        if user:
            raise ValidationError('That username is taken. Please enter a different one.')

    def validate_email(self, email):
        """Checks if the email address already exists in the database."""

        # Query the database to see if the given email address is already present
        user = User.query.filter_by(email=email.data).first()

        if user:
            raise ValidationError('That email address is taken. Please enter a different one.')


class LoginForm(FlaskForm):
    """
    Defines the Flask form elements for the "Login" page.  The "Remember Me" element will be properly implemented later.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    """
    Defines the form elements to update user attributes on the "My Account" page, including changing one's username,
    email address, and uploading a new/different profile picture.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        # If the entered username is different from the stored one, check if the new name is already in the database
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please enter a different one.')

    def validate_email(self, email):
        # If the entered email address is different from the stored one, check if the new email is already in the DB
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email address is taken. Please enter a different one.')
