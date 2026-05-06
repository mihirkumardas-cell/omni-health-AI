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


DEFAULT_HOSPITALS = [
    {
        "name": "AIIMS Bhubaneswar",
        "address": "Sijua, Patrapada, Bhubaneswar, Odisha 751019",
        "specialty": "General, Heart, Liver, Diabetes",
        "phone": "(0674) 2476789",
        "description": "Tertiary care institute in South Bhubaneswar.",
        "city": "Bhubaneswar",
        "locality": "Patrapada",
        "heart_score": 94,
        "liver_score": 89,
        "diabetes_score": 90
    },
    {
        "name": "AMRI Hospitals Bhubaneswar",
        "address": "Plot No. 1, Near Jayadev Vatika Park, Khandagiri, Bhubaneswar, Odisha 751019",
        "specialty": "General, Heart, Liver, Diabetes",
        "phone": "0674-6666600",
        "description": "Tertiary care hospital in Khandagiri.",
        "city": "Bhubaneswar",
        "locality": "Khandagiri",
        "heart_score": 90,
        "liver_score": 83,
        "diabetes_score": 86
    },
    {
        "name": "Apollo Hospitals Bhubaneswar",
        "address": "Plot No. 251, Old Sainik School Road, Gajapati Nagar, Bhubaneswar, Odisha 750015",
        "specialty": "Heart, Liver, Diabetes, General",
        "phone": "0674-6661016",
        "description": "Large multispecialty hospital with cardiac and gastro services.",
        "city": "Bhubaneswar",
        "locality": "Gajapati Nagar",
        "heart_score": 94,
        "liver_score": 84,
        "diabetes_score": 88
    },
    {
        "name": "Ashwini Hospital",
        "address": "CDA, Sector 1, Cuttack, Odisha 753014",
        "specialty": "General",
        "phone": "+91 92380 08811",
        "description": "General hospital in CDA Sector 1, Cuttack.",
        "city": "Cuttack",
        "locality": "CDA Sector 1",
        "heart_score": 68,
        "liver_score": 64,
        "diabetes_score": 66
    },
    {
        "name": "CARE Hospitals Bhubaneswar",
        "address": "Unit No.42, Plot No.324, Prachi Enclave Rd, Rail Vihar, Chandrasekharpur, Bhubaneswar, Odisha 751016",
        "specialty": "Heart, Diabetes, General",
        "phone": "0674-6165656",
        "description": "Specialty-led hospital in Chandrasekharpur.",
        "city": "Bhubaneswar",
        "locality": "Chandrasekharpur",
        "heart_score": 93,
        "liver_score": 78,
        "diabetes_score": 87
    },
    {
        "name": "Hi-Tech Hospital Bhubaneswar",
        "address": "Pandara, Rasulgarh, Bhubaneswar, Odisha",
        "specialty": "General, Heart, Diabetes",
        "phone": "0674-3500900",
        "description": "Multi-specialty hospital with cardiology and critical care services.",
        "city": "Bhubaneswar",
        "locality": "Rasulgarh",
        "heart_score": 85,
        "liver_score": 77,
        "diabetes_score": 83
    },
    {
        "name": "Hope Hospital",
        "address": "Mangalabag, Cuttack, Odisha",
        "specialty": "General",
        "phone": "+91-9437196408",
        "description": "Local general hospital serving central Cuttack.",
        "city": "Cuttack",
        "locality": "Mangalabag",
        "heart_score": 66,
        "liver_score": 63,
        "diabetes_score": 65
    },
    {
        "name": "KIMS Hospital Bhubaneswar",
        "address": "Kushabhadra Campus, KIIT Campus 5, Patia, Bhubaneswar, Odisha 751024",
        "specialty": "General, Heart, Liver, Diabetes",
        "phone": "0674-7111000",
        "description": "Large academic and multispecialty hospital in Patia.",
        "city": "Bhubaneswar",
        "locality": "Patia",
        "heart_score": 89,
        "liver_score": 85,
        "diabetes_score": 86
    },
    {
        "name": "Padmini Care Hospital",
        "address": "DRIEMS Road, Kotasahi, Tangi, Odisha 754022",
        "specialty": "General, Heart, Liver, Diabetes",
        "phone": "0671-2595222 / 9776000399",
        "description": "Multispecialty hospital in Tangi, Cuttack with cardiology, gastroenterology, general medicine, emergency and diagnostic services.",
        "city": "Cuttack",
        "locality": "Tangi",
        "heart_score": 82,
        "liver_score": 80,
        "diabetes_score": 78
    },
    {
        "name": "Ratna Hospital",
        "address": "Fandi Road, Mangalabag, Cuttack 753001",
        "specialty": "Orthopedic, General",
        "phone": "+91-9437268144",
        "description": "Private hospital in Mangalabag; stronger general recommendation than specialty-specific fit.",
        "city": "Cuttack",
        "locality": "Mangalabag",
        "heart_score": 62,
        "liver_score": 60,
        "diabetes_score": 61
    },
    {
        "name": "SCB Medical College & Hospital",
        "address": "Manglabag, Cuttack, Odisha 753007",
        "specialty": "General, Heart, Liver, Diabetes",
        "phone": "0671-2414080",
        "description": "Government multi-specialty teaching hospital in Cuttack.",
        "city": "Cuttack",
        "locality": "Mangalabag",
        "heart_score": 90,
        "liver_score": 84,
        "diabetes_score": 86
    },
    {
        "name": "SUM Ultimate Medicare",
        "address": "K-8, Kalinga Nagar, Ghatikia, Bhubaneswar, Odisha 751003",
        "specialty": "General, Heart, Liver, Diabetes",
        "phone": "+91-0674-3500500",
        "description": "Major quaternary care hospital in Ghatikia.",
        "city": "Bhubaneswar",
        "locality": "Ghatikia",
        "heart_score": 92,
        "liver_score": 86,
        "diabetes_score": 88
    },
    {
        "name": "SUN Hospitals",
        "address": "Kanika Rd, Srivihar Colony, Tulsipur, Cuttack, Odisha 753008",
        "specialty": "General, Heart, Diabetes",
        "phone": "+91-7205715067",
        "description": "Large multispecialty hospital on Kanika Road, Cuttack.",
        "city": "Cuttack",
        "locality": "Tulsipur",
        "heart_score": 86,
        "liver_score": 74,
        "diabetes_score": 84
    },
    {
        "name": "Shanti Memorial Hospital",
        "address": "Patnaik Colony, Thoria Sahi, Cuttack 753001",
        "specialty": "General, Heart, Diabetes",
        "phone": "0671-2415250",
        "description": "Multi-specialty hospital in central Cuttack.",
        "city": "Cuttack",
        "locality": "Patnaik Colony",
        "heart_score": 84,
        "liver_score": 72,
        "diabetes_score": 81
    },
    {
        "name": "South Point Hospital",
        "address": "Ring Rd, behind Indian Oil petrol pump, Arunodaya Nagar, Cuttack, Odisha 753012",
        "specialty": "General, Heart",
        "phone": "+91-7008399483",
        "description": "NABH-accredited multi-specialty hospital in Arunodaya Nagar.",
        "city": "Cuttack",
        "locality": "Arunodaya Nagar",
        "heart_score": 82,
        "liver_score": 70,
        "diabetes_score": 75
    }
]


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


def seed_default_hospitals():
    if Hospital.query.count() > 0:
        return
    db.session.add_all(Hospital(**hospital) for hospital in DEFAULT_HOSPITALS)
    db.session.commit()


def initialize_database():
    db.create_all()
    inspector = inspect(db.engine)
    if "hospital" in inspector.get_table_names():
        _ensure_hospital_columns()
        seed_default_hospitals()
    if not Admin.query.filter_by(username="admin").first():
        default_admin = Admin(username="admin", password="admin123")
        db.session.add(default_admin)
        db.session.commit()
