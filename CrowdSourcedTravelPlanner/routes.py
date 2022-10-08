from CrowdSourcedTravelPlanner import app, forms
from flask import render_template, url_for, flash, redirect


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    """
    Flask template for the "Register" page. Validates user input and displays helpful messages if the user enters
    invalid or missing data.  Upon successfully registering the user will be redirected to the "Landing" page and a
    green success alert will be shown.  For testing purposes, a successful login can be simulated by entering any valid
    text in each of the form fields.
    """
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account Created for {form.username.data}!', 'success')
        return redirect(url_for('landing'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    Flask template for the "Register" page. Upon successfully logging in, the user will be redirected to the "Landing"
    page and a green success alert will be shown.  A red error alert will be shown for unsuccessful login attempts.
    For testing purposes, only the credentials 'admin@blog.com' and 'password' will successfully log in.  All other
    inputs will result in an unsuccessful login.
    """
    form = forms.LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('landing'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Log In', form=form)
