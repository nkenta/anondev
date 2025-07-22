from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    openai_api_key = db.Column(db.String(200), nullable=True)
    reports = db.relationship('ReportHistory', backref='author', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ReportHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_text = db.Column(db.Text, nullable=False)
    anonymized_text_highlighted = db.Column(db.Text, nullable=False)
    anonymized_text_clean = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Add a server_default to handle existing rows during migration.
    model_used = db.Column(db.String(50), nullable=False, server_default='unknown')
    anonymization_level = db.Column(db.String(50), nullable=False, server_default='unknown')

    def __repr__(self):
        return f'<ReportHistory {self.id}>'