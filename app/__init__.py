from flask import Flask
from .extensions import mongo
from .webhook.routes import webhook

# Creating our flask app
def create_app():

    app = Flask(__name__)
    
    app.config["MONGO_URI"] = "mongodb://localhost:27017/github_events"

    mongo.init_app(app)

    # registering all the blueprints
    app.register_blueprint(webhook)

    return app
