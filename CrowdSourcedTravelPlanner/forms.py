from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DecimalField, \
    RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from CrowdSourcedTravelPlanner.models import User
from flask_login import current_user
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import Field
from wtforms.widgets import TextInput


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
    email address, location, and uploading a new/different profile picture.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    location = StringField('Location')
    sort = RadioField('Sort',
                      choices=[('recent', 'Recently Added Experiences'), ('top_rated', 'Top Rated Experiences')],
                      validators=[DataRequired()])
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


class KeywordListField(Field):
    """
    Custom field used to display a text box in which the user can enter multiple comma-delineated keywords.
    The form then parses the user-entered string and returns a list of keyword strings.  Adapted from
    https://wtforms.readthedocs.io/en/2.3.x/fields/.
    """
    widget = TextInput()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []


class ExperienceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    picture = FileField('Upload Experience Picture', validators=[FileAllowed(['jpg', 'png'])])

    # Rating selection dropdown to allow the user to optionally rate their new Experience
    star_rating = SelectField('Your Rating',
                              choices=[(0, 'Select'), (1, '1 - Very Bad'), (2, '2 - Bad'), (3, '3 - Average'),
                                       (4, '4 - Good'), (5, '5 - Very Good')], coerce=int)

    # At least 1 keyword is required for now during testing.  In the future we can decide if keywords will actually be
    # required.
    keywords = KeywordListField('Keywords (Please separate multiple keywords with commas)', validators=[DataRequired()])
    submit = SubmitField('Post')


class SearchForm(FlaskForm):
    search_type = SelectField('Search by', choices=[('location', 'Location'), ('keyword', 'Keyword')])
    search_string = StringField('Search String', validators=[DataRequired()])
    submit = SubmitField('Search')


class CreateTripForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    picture = FileField('Upload Trip Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Create Trip')


class RatingForm(FlaskForm):
    star_rating = SelectField('Your Rating',
                              choices=[(0, 'Select'), (1, '1 - Very Bad'), (2, '2 - Bad'), (3, '3 - Average'),
                                       (4, '4 - Good'), (5, '5 - Very Good')], coerce=int)
    submit = SubmitField('Submit')
