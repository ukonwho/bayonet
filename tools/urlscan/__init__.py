from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import BayonetConfig

APP = Flask(__name__)
APP.config.from_object(BayonetConfig)
DB = SQLAlchemy(APP, session_options={'autocommit': True})
