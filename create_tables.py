# create_tables.py - Create all database tables using SQLAlchemy

from flask import Flask
from models import db

app = Flask(__name__)

# Basic app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables using app context
with app.app_context():
    db.create_all()
    print("✅ All tables created successfully.") 