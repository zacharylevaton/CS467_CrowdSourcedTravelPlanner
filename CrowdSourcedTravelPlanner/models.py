from datetime import datetime
from CrowdSourcedTravelPlanner import db, login_manager
from flask_login import UserMixin
from sqlalchemy_utils import aggregated


@login_manager.user_loader
def load_user(user_id):
    """
    Obtains the database info for the User with the given user_id, as described in
    https://flask-login.readthedocs.io/en/latest/.
    """
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    Defines the database attributes for the site's users.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    date_account_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    experiences = db.relationship('Experience', backref='author', lazy=True)
    trips = db.relationship('Trip', backref='author', lazy=True)
    location = db.Column(db.String(100), nullable=True, default="")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    sort = db.Column(db.String(20), nullable=True, default='recent')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Keyword(db.Model):
    """
    Defines the database attributes for the keywords that can be used to tag Experiences. Used in forming a relationship
    between Experiences and Keywords.
    """
    __tablename__ = "keywords"
    id = db.Column(db.Integer, primary_key=True)
    keyword_text = db.Column(db.String, nullable=False)
    experience_id = db.Column(db.Integer, db.ForeignKey('experience.id'))

    experience = db.relationship("Experience", back_populates="keywords")

    def __repr__(self):
        return f"Keyword('{self.keyword_text}')"


class Experience(db.Model):
    """
    Defines the database attributes for user-submitted travel Experiences.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    keywords = db.relationship('Keyword', order_by=Keyword.id, back_populates='experience')

    # Average rating attribute code adapted from https://sqlalchemy-utils.readthedocs.io/en/latest/aggregates.html.
    @aggregated('ratings', db.Column(db.Numeric))
    def avg_rating(self):
        return db.func.avg(Rating.stars)

    ratings = db.relationship("Rating")

    def __repr__(self):
        return f"Experience('{self.title}', '{self.date_posted}')"


class Trip(db.Model):
    """
    Defines the database attributes for user-submitted Trips.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='trips_default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Trip('{self.title}', '{self.location}', '{self.image_file}')"


class TripExperience(db.Model):
    """
    Defines the database attributes for the cross-reference table for trips and experiences.
    """
    id = db.Column(db.Integer, primary_key=True)
    exp_id = db.Column(db.Integer, db.ForeignKey('experience.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)

    def __repr__(self):
        return f"TripExperience('{self.exp_id}', '{self.trip_id}')"


class Rating(db.Model):
    """
    Defines the database attributes for a user's rating of an Experience.  Used to calculate the average rating of the
    Experience.  Code adapted from https://sqlalchemy-utils.readthedocs.io/en/latest/aggregates.html.
    """
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key=True)
    stars = db.Column(db.Integer)   # Star rating entered in the form on the Experience Details page
    experience_id = db.Column(db.Integer, db.ForeignKey('experience.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))   # Database ID of currently logged-in user

    def __repr__(self):
        return f"Rating('Experience: {self.experience_id}', 'User: {self.user_id}', 'Stars: {self.stars}')"
