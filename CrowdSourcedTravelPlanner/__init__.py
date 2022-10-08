from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e801c73c9d2a7799c216c458ab9f6235'

from CrowdSourcedTravelPlanner import routes