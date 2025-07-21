from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resume_filename = db.Column(db.String(255))
    preferred_title = db.Column(db.String(255))
    preferred_location = db.Column(db.String(255))

    user = db.relationship("User", backref="profile") 

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_title = db.Column(db.String(255))
    company = db.Column(db.String(100))
    link = db.Column(db.String(500))
    status = db.Column(db.String(50))  # 'applied', 'manual'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="applications") 