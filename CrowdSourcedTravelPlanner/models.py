from datetime import datetime
from CrowdSourcedTravelPlanner import db, login_manager
from flask_login import UserMixin


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
    location = db.Column(db.String(100), nullable=True, default="")
    latitude = db.Column(db.Float, nullable=True)  # Temporarily nullable for now while I'm testing
    longitude = db.Column(db.Float, nullable=True)  # Re-evaluate later
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
    rating = db.Column(db.Float, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=True)  # Temporarily nullable for now while I'm testing
    longitude = db.Column(db.Float, nullable=True)  # Re-evaluate later
    keywords = db.relationship('Keyword', order_by=Keyword.id, back_populates='experience')

    def __repr__(self):
        return f"Experience('{self.title}', '{self.date_posted}')"
