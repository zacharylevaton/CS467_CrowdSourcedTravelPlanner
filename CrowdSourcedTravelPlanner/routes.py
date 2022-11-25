from CrowdSourcedTravelPlanner import app, forms, db, bcrypt
from flask import render_template, url_for, flash, redirect, request, abort, make_response
from CrowdSourcedTravelPlanner.models import User, Experience, Keyword, Trip, TripExperience, Rating
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import and_
import os
import secrets
from PIL import Image
import requests
import urllib.parse
import folium


# Context processor passes data to the page layout template
@app.context_processor
def inject_data():
    trip_data = Trip.query.order_by(Trip.title.asc()).all()
    trip_data_count = Trip.query.count()
    experience_data = Experience.query.order_by(Experience.title.asc()).all()
    exp_data_count = Experience.query.count()
    return dict(trip_data=trip_data, trip_data_count=trip_data_count, experience_data=experience_data,
                exp_data_count=exp_data_count)


# Landing page
@app.route('/')
@app.route("/landing")
def landing():
    # Set page number for pagination
    page = request.args.get('page', 1, type=int)
    nearby_page = request.args.get('nearby_page', 1, type=int)

    # If no user is currently logged in, get all experiences and sort by date created in descending order
    if not current_user.is_authenticated:
        experiences = Experience.query.order_by(Experience.date_posted.desc()).paginate(page=page, per_page=5)
        return render_template('landing.html', experiences=experiences)

    # Check if user has set sort to "most recent"
    if current_user.sort == 'recent':
        experiences = Experience.query.order_by(Experience.date_posted.desc()).paginate(page=page, per_page=3)

    # Check if user has set sort to "top-rated"
    if current_user.sort == 'top_rated':
        experiences = Experience.query.order_by(Experience.avg_rating.desc()).paginate(page=page, per_page=3)

    # Check if user is logged in and set their location
    if current_user.is_authenticated and current_user.location != "":
        # Get all nearby experiences (under ~35 miles)
        nearby_experiences = Experience.query.filter(
            and_(Experience.longitude - current_user.longitude < 0.5, Experience.latitude - current_user.latitude < 0.5,
                 current_user.longitude - Experience.longitude < 0.5,
                 current_user.latitude - Experience.latitude < 0.5)).paginate(
            page=nearby_page, per_page=3)
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
    # Set page number for pagination
    experience_page = request.args.get('experience_page', 1, type=int)
    trip_page = request.args.get('trip_page', 1, type=int)

    # Get all the experiences created by the currently logged-in user
    experiences = Experience.query.filter(Experience.author == current_user).paginate(page=experience_page, per_page=3)
    experiences_query = Experience.query.filter(Experience.author == current_user)
    exp_count = experiences_query.count()

    # Get all trips created by the currently logged-in user
    trips = Trip.query.filter(Trip.author == current_user).paginate(page=trip_page, per_page=3)
    trips_query = Trip.query.filter(Trip.author == current_user)
    trip_count = trips_query.count()

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', title='My Profile', image_file=image_file, experiences=experiences,
                           exp_count=exp_count, trips=trips, trip_count=trip_count)


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
        current_user.sort = form.sort.data

        # Get the latitude and longitude of the address entered on the form
        if current_user.location != "":
            geolocation = get_geolocation(current_user.location)

            # Update the User attributes with the latitude and longitude if values are found
            if geolocation:
                current_user.latitude = round(float(geolocation[0]), 4)
                current_user.longitude = round(float(geolocation[1]), 4)

        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.location.data = current_user.location
        form.sort.data = current_user.sort

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
    url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) + '?format=json'

    response = requests.get(url).json()

    if response:
        return response[0]["lat"], response[0]["lon"]
    else:
        return '-200', '-200'  # '-200' is outside the valid range and is used as a flag if no valid results are found


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
                                image_file=picture_file, author=current_user)

        # Get the latitude and longitude of the address entered on the form
        geolocation = get_geolocation(experience.location)
        # Update the Experience with the latitude and longitude if values are found
        if geolocation:
            experience.latitude = round(float(geolocation[0]), 4)  # Rounding Lat/Long to 4 decimal places for now
            experience.longitude = round(float(geolocation[1]), 4)  # We can change it later if we need to

        # The form returns a list of keywords.  Use the list to create new Keyword objects and set the Experience's
        # keywords field.
        received_keywords = form.keywords.data
        keyword_list = []

        for current_keyword in received_keywords:
            keyword_list.append(Keyword(keyword_text=current_keyword))
        experience.keywords = keyword_list

        # Save the star rating for the Experience if the user has selected a score
        star_rating = form.star_rating.data

        if star_rating > 0:
            experience.ratings.append(Rating(stars=star_rating, experience_id=experience.id, user_id=current_user.id))

        # Add the new Experience to the database
        db.session.add(experience)
        db.session.commit()

        # Redirect to the Landing page after successful Experience creation
        flash('Your Experience has been created!', 'success')
        return redirect(url_for('landing'))

    return render_template('create_experience.html', title='Add Experience', form=form, legend='Add Experience',
                           display_image=display_image)


# Experience Details page
@app.route("/experience/<int:experience_id>", methods=['GET', 'POST'])
def experience(experience_id):
    experience = Experience.query.get_or_404(experience_id)

    # Generate Folium map. Code adapted from
    # https://stackoverflow.com/questions/37379374/insert-the-folium-maps-into-the-jinja-template/60031784#60031784
    folium_map = None
    if experience.latitude != -200 and experience.longitude != -200:
        start_coords = (experience.latitude, experience.longitude)
        folium_map = folium.Map(location=start_coords, zoom_start=10)
        popup = folium.Popup("<p><strong>" + experience.title + "</strong></p><p>" + experience.location + "</p>",
                             max_width=300)
        folium.Marker(location=start_coords, popup=popup, tooltip="Click for more information").add_to(folium_map)
        folium_map.save('CrowdSourcedTravelPlanner/templates/map.html')

    # Check if the logged-in user has already rated the Experience
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(experience_id=experience.id, user_id=current_user.id).first()
        if user_rating:
            rating_form = forms.RatingForm(star_rating=user_rating.stars)
        else:
            rating_form = forms.RatingForm()
    else:
        rating_form = forms.RatingForm()

    if rating_form.validate_on_submit():
        star_rating = rating_form.star_rating.data

        if user_rating:  # If the logged-in user is changing their previous rating for the Experience
            # If the user picks "Select" from the dropdown, it signals that they are removing their rating.
            if star_rating == 0:
                db.session.delete(user_rating)  # Remove the user's rating so that it no longer affects the average
            else:
                user_rating.stars = star_rating  # Update the user's score for the Experience
        # Otherwise, add the new rating to the list of ratings for the Experience
        else:
            experience.ratings.append(Rating(stars=star_rating, experience_id=experience.id, user_id=current_user.id))

        # Save the changes to the database
        db.session.commit()

        # Flash a message indicating that the rating was saved
        flash(f'Your rating was saved!', 'success')
        return redirect(url_for('experience', experience_id=experience.id))

    return render_template('experience.html', title=experience.title, experience=experience, rating_form=rating_form,
                           folium_map=folium_map)


# Folium map display
@app.route('/map')
def map():
    return render_template('map.html')


# Update Experience page
@app.route("/experience/<int:experience_id>/update", methods=['GET', 'POST'])
@login_required
def update_experience(experience_id):
    experience = Experience.query.get_or_404(experience_id)
    display_image = experience.image_file

    # Make sure only the Experience's author can update it
    if experience.author != current_user:
        abort(403)

    # Check if the logged-in user has already rated the Experience
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(experience_id=experience.id, user_id=current_user.id).first()
        if user_rating:
            form = forms.ExperienceForm(star_rating=user_rating.stars)
        else:
            form = forms.ExperienceForm()
    else:
        form = forms.ExperienceForm()
    form.submit.label.text = 'Update'

    # Update the Experience details after form submission
    if form.validate_on_submit():
        # If the user updates the Experience image, save it to the file system
        if form.picture.data:
            picture_file = save_experience_picture(form.picture.data)
            experience.image_file = picture_file

        experience.title = form.title.data
        experience.description = form.description.data
        experience.location = form.location.data

        # Get the latitude and longitude of the address entered on the form
        geolocation = get_geolocation(experience.location)
        # Update the Experience with the latitude and longitude if values are found
        if geolocation:
            experience.latitude = round(float(geolocation[0]), 4)  # Rounding Lat/Long to 4 decimal places for now
            experience.longitude = round(float(geolocation[1]), 4)  # We can change it later if we need to

        # The form returns a list of keywords.  Use the list to create new Keyword objects and set the Experience's
        # keywords field.
        received_keywords = form.keywords.data
        keyword_list = []

        for current_keyword in received_keywords:
            keyword_list.append(Keyword(keyword_text=current_keyword))
        experience.keywords = keyword_list

        # Save the user's star rating for their Experience if they have selected one
        star_rating = form.star_rating.data

        if user_rating:  # If the logged-in user is changing their previous rating for the Experience
            # If the user picks "Select" from the dropdown, it signals that they are removing their rating.
            if star_rating == 0:
                db.session.delete(user_rating)  # Remove the user's rating so that it no longer affects the average
            else:
                user_rating.stars = star_rating  # Update the user's score for the Experience
        # Otherwise, add the new rating to the list of ratings for the Experience
        else:
            experience.ratings.append(Rating(stars=star_rating, experience_id=experience.id, user_id=current_user.id))

        # Save changes to the database
        db.session.commit()
        flash('Your Experience has been updated!', 'success')
        return redirect(url_for('experience', experience_id=experience.id))
    elif request.method == 'GET':
        # Populate form with existing values
        form.title.data = experience.title
        form.description.data = experience.description
        form.location.data = experience.location

        # Pre-fill the "Keywords" field by concatenating any existing keywords into a single string
        display_list = []
        for current_keyword in experience.keywords:
            display_list.append(current_keyword.keyword_text)
        form.keywords.data = display_list

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
    experiences = Experience.query.filter_by(author=user) \
        .order_by(Experience.date_posted.desc()) \
        .paginate(page=page, per_page=5)
    return render_template('user_experiences.html', experiences=experiences, user=user)


# Search Experiences
@app.route("/search", methods=['GET', 'POST'])
def search():
    form = forms.SearchForm()

    # Query the database for all Experiences with valid locations
    map_experiences = Experience.query.filter(Experience.latitude != -200, Experience.longitude != -200).all()

    # Populate world map with selectable markers for all found Experiences
    folium_map = folium.Map(location=[0, 0], zoom_start=2)

    for exp in map_experiences:
        # Set details for each marker's location, popup, and tooltip text
        exp_coords = (exp.latitude, exp.longitude)
        popup_text = "<a href='" + url_for('experience', experience_id=exp.id) \
                     + "' target='_blank' rel='noopener noreferrer'>" + exp.title + "</a><br><br>" + exp.location \
                     + "<br><br><a href='" + url_for('experience', experience_id=exp.id) \
                     + "' target='_blank' rel='noopener noreferrer'><img class='img-rounded' src='" \
                     + url_for('static', filename='experience_pics/' + exp.image_file) + "' width='200'></a>"
        popup = folium.Popup(popup_text, min_width=100, max_width=300)
        tooltip = folium.Tooltip("<p><strong>" + exp.title + "</strong></p><p>" + exp.location
                                 + "</p><p>Click for more information</p>")
        folium.Marker(location=exp_coords, popup=popup, tooltip=tooltip).add_to(folium_map)

    folium_map.save('CrowdSourcedTravelPlanner/templates/map.html')

    # Display results after submitting Search form
    if form.validate_on_submit():
        search_type = form.search_type.data
        search_string = form.search_string.data

        # Set page number for pagination
        page = request.args.get('page', 1, type=int)

        # Get Experience results depending on whether search is by location or keyword
        if search_type == 'location':
            experiences = Experience.query.filter(Experience.location.like('%' + search_string + '%')) \
                .order_by(Experience.title) \
                .paginate(page=page, per_page=5)
        elif search_type == 'keyword':
            experiences = Experience.query \
                .filter(Experience.keywords.any(Keyword.keyword_text.like('%' + search_string + '%'))) \
                .order_by(Experience.title) \
                .paginate(page=page, per_page=5)

        return render_template('search_results.html', experiences=experiences, search_type=search_type,
                               search_string=search_string)

    # Render original Search form
    return render_template('search.html', form=form)


# Keyword Link page
@app.route("/keyword/<string:keyword_text>")
def keyword(keyword_text):
    # Set page number for pagination
    page = request.args.get('page', 1, type=int)

    # Query for all the Experiences tagged with the received keyword
    experiences = Experience.query \
        .filter(Experience.keywords.any(Keyword.keyword_text.like('%' + keyword_text + '%'))) \
        .order_by(Experience.title) \
        .paginate(page=page, per_page=5)
    return render_template('keyword.html', experiences=experiences, keyword_text=keyword_text)


def save_trip_picture(form_picture):
    """Saves a user-uploaded image to the Trip pictures folder and gives it a random filename."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)  # Get the original extension of the uploaded image
    picture_fn = random_hex + f_ext

    # Save the image file to the pictures folder
    picture_path = os.path.join(app.root_path, 'static/trip_pics', picture_fn)

    # Resize large images before saving
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    # Return the filename of the newly saved image
    return picture_fn


# Trip Details page
@app.route("/trip/<int:trip_id>")
def trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)

    # Retrieve all Experiences contained within the Trip
    trip_experiences = db.session.query(Experience, TripExperience).select_from(Experience).join(TripExperience). \
        group_by(Experience.id).all()
    experiences = []
    for te in trip_experiences:
        experiences.append(te[0])

    return render_template('trip.html', title=trip.title, trip=trip, experiences=experiences)


# Create trip page.
@app.route("/trip/create", methods=['GET', 'POST'])
@login_required
def create_trip():
    form = forms.CreateTripForm()
    display_image = 'trip_default.jpg'

    if form.validate_on_submit():
        # Save the user-uploaded image to the file system
        if form.picture.data:
            picture_file = save_trip_picture(form.picture.data)
        else:
            picture_file = 'trip_default.jpg'

        trip = Trip(title=form.title.data, location=form.location.data, image_file=picture_file, author=current_user)

        # Add the new Trip to the database
        db.session.add(trip)
        db.session.commit()

        # Redirect to the Profile page after successful Trip creation
        flash('Your Trip has been created!', 'success')
        return redirect(url_for('profile'))

    return render_template('create_trip.html', title='Create Trip', form=form, display_image=display_image,
                           legend='Create Trip')


# Update trip page.
@app.route("/trip/<int:trip_id>/update", methods=['POST'])
@login_required
def update_trip(trip_id):
    form = forms.SearchForm()

    # Make sure only the Trip's author can update it.
    trip = Trip.query.get_or_404(trip_id)
    if trip.author != current_user:
        abort(403)

    # Find and extract all information for experiences already added to current trip.
    trip_experience = TripExperience.query.filter_by(trip_id=trip_id)
    added_experiences = dict()
    for te in trip_experience:
        added_experiences[te.exp_id] = Experience.query.get(te.exp_id)

    # Default values for form submittal.
    search_type = search_string = experiences = None

    if request.values and form.validate_on_submit():
        search_type = form.search_type.data
        search_string = form.search_string.data

        # Set page number for pagination
        page = request.args.get('page', 1, type=int)

        # Get Experience results depending on whether search is by location or keyword
        if search_type == 'location':
            experiences = Experience.query.filter(Experience.location.like('%' + search_string + '%')) \
                .order_by(Experience.title) \
                .paginate(page=page, per_page=5)
        elif search_type == 'keyword':
            experiences = Experience.query \
                .filter(Experience.keywords.any(Keyword.keyword_text.like('%' + search_string + '%'))) \
                .order_by(Experience.title) \
                .paginate(page=page, per_page=5)

    return render_template('update_trip.html', form=form, experiences=experiences, search_type=search_type,
                           search_string=search_string, trip=trip, added_experiences=added_experiences)


# Jquery POST route to add experience to trip.
@app.route("/add_experience_to_trip", methods=['POST'])
def add_experience_to_trip():
    if request.form['expID'] and request.form['tripID']:
        # Create a new Experience object and set the author to the current user.
        trip_experience = TripExperience(exp_id=request.form['expID'], trip_id=request.form['tripID'])

        # Add the new TripExperience relationship to the database.
        db.session.add(trip_experience)
        db.session.commit()

        return "Success"
    return "Failure"


# Jquery POST route to delete experience from trip.
@app.route("/delete_experience_from_trip", methods=['POST'])
def delete_experience_from_trip():
    if request.form['expID'] and request.form['tripID']:
        # Create a new Experience object and set the author to the current user.
        trip_experience = db.session.query(TripExperience). \
            filter(TripExperience.exp_id == request.form['expID']). \
            filter(TripExperience.trip_id == request.form['tripID']).one()

        # Add the new TripExperience relationship to the database.
        db.session.delete(trip_experience)
        db.session.commit()

        return "Success"
    return "Failure"


# Delete Trip button
@app.route("/trip/<int:trip_id>/delete", methods=['POST'])
@login_required
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)

    # Make sure only the Trip's author can delete it
    if trip.author != current_user:
        abort(403)

    # Delete the Trip and redirect to the Landing page
    db.session.delete(trip)
    db.session.commit()
    flash('Your Trip has been deleted!', 'success')
    return redirect(url_for('profile'))


# User Trips page
@app.route("/user-trips/<string:username>")
def user_trips(username):
    # Set page number for pagination
    page = request.args.get('page', 1, type=int)

    # Find the username of the User
    user = User.query.filter_by(username=username).first_or_404()

    # Query for all the Trips created by the selected user
    trips = Trip.query.filter_by(author=user) \
        .order_by(Trip.title.desc()) \
        .paginate(page=page, per_page=5)
    return render_template('user_trips.html', trips=trips, user=user)
