from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import inspect, text

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    symptom_entries = db.relationship('SymptomEntry', backref='user', lazy=True)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    specialty = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(400), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    locality = db.Column(db.String(120), nullable=True)
    heart_score = db.Column(db.Integer, nullable=False, default=60)
    liver_score = db.Column(db.Integer, nullable=False, default=60)
    diabetes_score = db.Column(db.Integer, nullable=False, default=60)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SymptomEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def _ensure_hospital_columns():
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("hospital")}
    additions = {
        "city": "ALTER TABLE hospital ADD COLUMN city VARCHAR(80)",
        "locality": "ALTER TABLE hospital ADD COLUMN locality VARCHAR(120)",
        "heart_score": "ALTER TABLE hospital ADD COLUMN heart_score INTEGER NOT NULL DEFAULT 60",
        "liver_score": "ALTER TABLE hospital ADD COLUMN liver_score INTEGER NOT NULL DEFAULT 60",
        "diabetes_score": "ALTER TABLE hospital ADD COLUMN diabetes_score INTEGER NOT NULL DEFAULT 60"
    }
    for column_name, statement in additions.items():
        if column_name not in columns:
            db.session.execute(text(statement))
    db.session.commit()


def initialize_database():
    db.create_all()
    inspector = inspect(db.engine)
    if "hospital" in inspector.get_table_names():
        _ensure_hospital_columns()
    if not Admin.query.filter_by(username="admin").first():
        default_admin = Admin(username="admin", password="admin123")
        db.session.add(default_admin)
        db.session.commit()
