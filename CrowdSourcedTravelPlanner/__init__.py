from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import timedelta

# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'e801c73c9d2a7799c216c458ab9f6235'  # Used in preventing cross-site scripting attacks
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=1)  # Store "Remember Me" cookie for 24 hours
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)  # Used for hashing user passwords
login_manager = LoginManager(app)  # Login manager settings to redirect to correct page after logging in
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from CrowdSourcedTravelPlanner import routes
