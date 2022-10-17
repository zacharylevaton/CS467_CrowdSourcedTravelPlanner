from CrowdSourcedTravelPlanner import app, forms, db, bcrypt
from flask import render_template, url_for, flash, redirect, request, abort
from CrowdSourcedTravelPlanner.models import User, Experience
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import and_
import os
import secrets
from PIL import Image
import requests
import urllib.parse


# Landing page
@app.route('/')
@app.route("/landing")
def landing():
    # Set page number for pagination
    page = request.args.get('page', 1, type=int)
    nearby_page = request.args.get('nearby_page', 1, type=int)

    # Get all experiences and sort by date created in descending order
    experiences = Experience.query.order_by(Experience.date_posted.desc()).paginate(page=page, per_page=3)

    # Check if user is logged in and set their location
    if current_user.is_authenticated and current_user.location != "":

            # Get all nearby experiences (under ~35 miles)
            nearby_experiences = Experience.query.filter(and_(Experience.longitude-User.longitude < 0.5, Experience.latitude-User.latitude < 0.5)).paginate(page=nearby_page, per_page=10)
            return render_template('landing.html', experiences=experiences, nearby_experiences=nearby_experiences)

    return render_template('landing.html', experiences=experiences)


# Register page
@app.route("/register", methods=['GET', 'POST'])
def register():
    """
    Flask template for the "Register" page. Validates user input and displays helpful messages if the user enters
    invalid or missing data.  User passwords are stored securely as hashes rather than plaintext.  Upon successfully
    registering the user will be redirected to the "Landing" page and a green success alert will be shown.
    """
    # Redirect to the Landing Page if the user is already logged in.
    if current_user.is_authenticated:
        return redirect(url_for('landing'))

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        # Generate a hash for the user-submitted password plaintext
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # Create a new User database entry
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)

        # Add user to the database
        db.session.add(user)
        db.session.commit()

        # Flash a message indicating that the account was created successfully
        flash(f'Account created for {form.username.data}.  You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# Login page
@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Flask template for the "Login" page. Upon successfully logging in, the user will be redirected to the "Landing"
    page and a green success alert will be shown.  A red error alert will be shown for unsuccessful login attempts.
    """
    # Redirect to the Landing page if the user is already logged in.
    if current_user.is_authenticated:
        return redirect(url_for('landing'))

    form = forms.LoginForm()
    if form.validate_on_submit():

        # Check if a user with the entered email address exists in the database
        user = User.query.filter_by(email=form.email.data).first()

        # Log the user in if their credentials are valid
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)

            # If the user was attempting to view a private page, redirect them to that page after logging in
            next_page = request.args.get('next')

            # Otherwise redirect them to the Landing page if the user is logging in directly from the "Log In" page
            return redirect(next_page) if next_page else redirect(url_for('landing'))

        # Otherwise, display a red message indicating that the login attempt was unsuccessful
        else:
            flash('Login Unsuccessful. Please check email address and password.', 'danger')
    return render_template('login.html', title='Log In', form=form)


# Log Out navbar item
@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('landing'))


# My Profile page
@app.route("/profile")
@login_required
def profile():
    # Get all the experiences created by the currently logged-in user
    experiences = Experience.query.filter(Experience.author == current_user)
    exp_count = experiences.count()

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', title='My Profile', image_file=image_file, experiences=experiences,
                           exp_count=exp_count)


def save_profile_picture(form_picture):
    """Saves a user-uploaded image to the profile pictures folder and gives it a random filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)  # Get the original extension of the uploaded image
    picture_fn = random_hex + f_ext

    # Save the image file to the pictures folder
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    # Resize large images before saving
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    # Return the filename of the newly saved image
    return picture_fn


# My Account page
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = forms.UpdateAccountForm()

    # Validate data entered by the user and update the user's info
    if form.validate_on_submit():
        # Save the user-uploaded image to the file system
        if form.picture.data:
            picture_file = save_profile_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.location = form.location.data
                
        # Get the latitude and longitude of the address entered on the form
        if current_user.location != "":
            geolocation = get_geolocation(current_user.location)

            # Update the User attributes with the latitude and longitude if values are found
            if geolocation:
                current_user.latitude = geolocation[0]
                current_user.longitude = geolocation[1]
        
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.location.data = current_user.location

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='My Account', image_file=image_file, form=form)


def save_experience_picture(form_picture):
    """Saves a user-uploaded image to the Experience pictures folder and gives it a random filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)  # Get the original extension of the uploaded image
    picture_fn = random_hex + f_ext

    # Save the image file to the pictures folder
    picture_path = os.path.join(app.root_path, 'static/experience_pics', picture_fn)

    # Resize large images before saving
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    # Return the filename of the newly saved image
    return picture_fn


def get_geolocation(address):
    """
    Returns a tuple of the latitude and longitude of the received address string.  Queries the Open Street Map database
    as described in https://stackoverflow.com/questions/25888396/how-to-get-latitude-longitude-with-python.
    """
    url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) +'?format=json'

    response = requests.get(url).json()

    return response[0]["lat"], response[0]["lon"]


# Add Experience page
@app.route("/experience/add", methods=['GET', 'POST'])
@login_required
def add_experience():
    form = forms.ExperienceForm()
    display_image = 'default.jpg'

    if form.validate_on_submit():
        # Save the user-uploaded image to the file system
        if form.picture.data:
            picture_file = save_experience_picture(form.picture.data)
        else:
            picture_file = 'default.jpg'

        # Create a new Experience object and set the author to the current user
        experience = Experience(title=form.title.data, location=form.location.data, description=form.description.data,
                                rating=form.rating.data, image_file=picture_file, author=current_user)

        # Get the latitude and longitude of the address entered on the form
        geolocation = get_geolocation(experience.location)
        # Update the Experience with the latitude and longitude if values are found
        if geolocation:
            experience.latitude = geolocation[0]
            experience.longitude = geolocation[1]

        # Add the new Experience to the database
        db.session.add(experience)
        db.session.commit()

        # Redirect to the Landing page after successful Experience creation
        flash('Your Experience has been created!', 'success')
        return redirect(url_for('landing'))

    return render_template('create_experience.html', title='Add Experience', form=form, legend='Add Experience',
                           display_image=display_image)


# Experience Details page
@app.route("/experience/<int:experience_id>")
def experience(experience_id):
    experience = Experience.query.get_or_404(experience_id)
    return render_template('experience.html', title=experience.title, experience=experience)


# Update Experience page
@app.route("/experience/<int:experience_id>/update", methods=['GET', 'POST'])
@login_required
def update_experience(experience_id):
    experience = Experience.query.get_or_404(experience_id)
    display_image = experience.image_file

    # Make sure only the Experience's author can update it
    if experience.author != current_user:
        abort(403)

    form = forms.ExperienceForm()

    # Update the Experience details after form submission
    if form.validate_on_submit():
        # If the user updates the Experience image, save it to the file system
        if form.picture.data:
            picture_file = save_experience_picture(form.picture.data)
            experience.image_file = picture_file

        experience.title = form.title.data
        experience.description = form.description.data
        experience.location = form.location.data
        experience.rating = form.rating.data

        # Get the latitude and longitude of the address entered on the form
        geolocation = get_geolocation(experience.location)
        # Update the Experience with the latitude and longitude if values are found
        if geolocation:
            experience.latitude = geolocation[0]
            experience.longitude = geolocation[1]

        db.session.commit()
        flash('Your Experience has been updated!', 'success')
        return redirect(url_for('experience', experience_id=experience.id))
    elif request.method == 'GET':
        # Populate form with existing values
        form.title.data = experience.title
        form.description.data = experience.description
        form.location.data = experience.location
        form.rating.data = experience.rating

    return render_template('create_experience.html', title='Update Experience', form=form, legend='Update Experience',
                           display_image=display_image)


# Delete Experience button
@app.route("/experience/<int:experience_id>/delete", methods=['POST'])
@login_required
def delete_experience(experience_id):

    # Edit: Delete button now works.  The Bootstrap fix is described in
    # https://stackoverflow.com/questions/65406733/bootstrap-modal-not-popping-up-when-clicking-button

    experience = Experience.query.get_or_404(experience_id)

    # Make sure only the Experience's author can delete it
    if experience.author != current_user:
        abort(403)

    # Delete the Experience and redirect to the Landing page
    db.session.delete(experience)
    db.session.commit()
    flash('Your Experience has been deleted!', 'success')
    return redirect(url_for('landing'))


# User Experiences page
@app.route("/user/<string:username>")
def user_experiences(username):
    # Set page number for pagination
    page = request.args.get('page', 1, type=int)

    # Find the username of the User
    user = User.query.filter_by(username=username).first_or_404()

    # Query for all the Experiences created by the selected user
    experiences = Experience.query.filter_by(author=user)\
        .order_by(Experience.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_experiences.html', experiences=experiences, user=user)
