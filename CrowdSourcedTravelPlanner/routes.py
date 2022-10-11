from CrowdSourcedTravelPlanner import app, forms, db, bcrypt
from flask import render_template, url_for, flash, redirect, request
from CrowdSourcedTravelPlanner.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required


# Landing page
@app.route('/')
@app.route("/landing")
def landing():
    return render_template('landing.html')


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
    return redirect(url_for('landing'))


# My Profile page
@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', title='My Profile')
