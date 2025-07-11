from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    openai_api_key = db.Column(db.String(100), default="")
    hf_api_key = db.Column(db.String(100), default="")
    is_admin = db.Column(db.Boolean, default=False)
    histories = db.relationship('History', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.Text, nullable=False)
    anonymised_text = db.Column(db.Text, nullable=False)
    anonymisation_level = db.Column(db.String(20), nullable=False)
    model_used = db.Column(db.String(20), nullable=False)
    input_filename = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f"<History {self.id} | {self.model_used} | {self.anonymisation_level}>"

# --- Flask-Login user_loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
