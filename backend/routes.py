from flask import render_template, request, redirect, url_for, flash, session
from models import db, Admin, User, Hospital, Feedback, SymptomEntry, seed_default_hospitals
from ml_models import predict_disease, predict_rnn
import re

VALID_HELP = {
    "heart": "Enter age, sex (1=male, 0=female), resting blood pressure, cholesterol, fasting blood sugar, max heart rate, and oldpeak.",
    "liver": "Enter age, total bilirubin, direct bilirubin, alkaline phosphatase, albumin, and total proteins.",
    "diabetes": "Enter pregnancies, glucose, blood pressure, skin thickness, insulin, and BMI."
}

SPECIALTY_MAP = {
    "heart": "Heart",
    "liver": "Liver",
    "diabetes": "Diabetes"
}

DISEASE_SCORE_FIELDS = {
    "heart": "heart_score",
    "liver": "liver_score",
    "diabetes": "diabetes_score"
}

NEARBY_CITY_MAP = {
    "cuttack": {"cuttack", "bhubaneswar"},
    "bhubaneswar": {"bhubaneswar", "cuttack"}
}

PREDICTION_FIELD_COUNTS = {
    "heart": 7,
    "liver": 6,
    "diabetes": 6
}

SYMPTOM_KEYWORDS = {
    "heart": [
        "chest pain", "shortness of breath", "palpitations", "high blood pressure", "fatigue", "dizziness", "cold sweat", "pressure"
    ],
    "liver": [
        "jaundice", "abdominal pain", "nausea", "vomiting", "dark urine", "itching", "loss of appetite", "bloating"
    ],
    "diabetes": [
        "thirst", "frequent urination", "hunger", "blurred vision", "slow healing", "weight loss", "tingling", "numbness"
    ]
}

PRESCRIPTIONS = {
    "heart": "Follow a low-sodium heart-healthy diet, monitor blood pressure, stay active, manage stress, and consult a cardiologist for medication review.",
    "liver": "Avoid alcohol, follow a balanced diet, drink plenty of water, and see a specialist for liver function monitoring and medication if needed.",
    "diabetes": "Control carbohydrate intake, exercise regularly, monitor blood glucose, and follow a diabetes care plan with medication or insulin as advised."
}

SYMPTOM_DESCRIPTIONS = {
    "heart": "Common heart concerns include chest pressure, shortness of breath, palpitations, and sudden fatigue.",
    "liver": "Liver issues often show as jaundice, abdominal discomfort, dark urine, nausea, and loss of appetite.",
    "diabetes": "Diabetes symptoms include excess thirst, frequent urination, blurred vision, fatigue, and slow wound healing."
}

CARE_ADVICE = {
    "heart": {
        "do": [
            "rest and avoid sudden exertion",
            "eat a low-sodium heart-healthy diet",
            "monitor your blood pressure regularly",
            "drink water and avoid caffeine when anxious"
        ],
        "dont": [
            "ignore chest pain or shortness of breath",
            "consume high-fat or salty foods",
            "skip medications or follow-up appointments",
            "smoke or use stimulants"
        ]
    },
    "liver": {
        "do": [
            "avoid alcohol",
            "eat light, balanced meals",
            "stay hydrated",
            "rest and avoid heavy physical strain"
        ],
        "dont": [
            "take unprescribed painkillers",
            "eat greasy or fried foods",
            "skip medical checkups",
            "ignore yellowing of the skin or eyes"
        ]
    },
    "diabetes": {
        "do": [
            "monitor your blood sugar",
            "eat regular meals with controlled carbs",
            "exercise moderately",
            "stay hydrated"
        ],
        "dont": [
            "consume sugary drinks or snacks",
            "skip insulin or medication doses",
            "ignore wounds or slow-healing sores",
            "delay seeing a doctor when symptoms worsen"
        ]
    }
}

MEDICINE_GUIDANCE = {
    "heart": [
        "doctor-prescribed heart medicines may include antiplatelets, statins, beta blockers, ACE inhibitors, or nitroglycerin depending on the condition",
        "do not self-start heart medicines without medical advice, especially if you have chest pain or breathlessness"
    ],
    "liver": [
        "avoid self-medicating because many medicines can affect the liver",
        "a doctor may use condition-specific medicines such as antivirals or steroids only after evaluating the cause of liver disease",
        "paracetamol and pain medicines should only be used within safe limits and with professional advice if you have liver problems"
    ],
    "diabetes": [
        "common prescribed diabetes medicines include metformin, other oral anti-diabetic medicines, GLP-1 medicines, or insulin depending on your blood sugar pattern",
        "do not start diabetes medicine on your own without checking blood sugar and speaking to a doctor"
    ]
}


def analyze_symptoms(symptoms_text):
    if not symptoms_text:
        return None, 0
    normalized = symptoms_text.lower()
    scores = {}
    for disease, keywords in SYMPTOM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                scores[disease] = scores.get(disease, 0) + 1
    if not scores:
        return None, 0
    best = max(scores, key=scores.get)
    confidence = min(90, 25 + scores[best] * 20)
    return best, confidence


def format_care_response(title, description, advice, confidence=None):
    lines = []
    if confidence is not None:
        lines.append(f"{title} ({confidence}% confidence)")
    else:
        lines.append(title)
    if description:
        lines.append(description)
    lines.append("")
    lines.append("Do:")
    lines.extend([f"- {item}" for item in advice["do"]])
    lines.append("")
    lines.append("Do not:")
    lines.extend([f"- {item}" for item in advice["dont"]])
    return "\n".join(lines)


def append_medicine_guidance(answer, disease):
    guidance = MEDICINE_GUIDANCE.get(disease)
    if not guidance:
        return answer
    medicine_lines = ["", "Possible medicine guidance:", *[f"- {item}" for item in guidance], "- ask a doctor or pharmacist before taking any medicine based on this suggestion"]
    return answer + "\n" + "\n".join(medicine_lines)


def normalize_location_text(value):
    if not value:
        return ""
    return re.sub(r"[^a-z0-9\s]", " ", value.lower()).strip()


def location_tokens(value):
    normalized = normalize_location_text(value)
    return {token for token in normalized.split() if len(token) > 2}


def compute_location_score(patient_location, hospital):
    patient_text = normalize_location_text(patient_location)
    if not patient_text:
        return 10, "location not provided"

    patient_tokens = location_tokens(patient_location)
    city = (hospital.city or "").lower()
    locality = (hospital.locality or "").lower()
    address_text = normalize_location_text(" ".join(filter(None, [hospital.locality, hospital.city, hospital.address])))

    if locality and locality in patient_text:
        return 30, f"same area: {hospital.locality}"
    if city and city in patient_text:
        return 22, f"same city: {hospital.city}"

    if city:
        for patient_city, nearby_cities in NEARBY_CITY_MAP.items():
            if patient_city in patient_text and city in nearby_cities:
                return 15, f"near {patient_city.title()}"

    overlap = patient_tokens.intersection(location_tokens(address_text))
    if overlap:
        return 12, f"address match: {', '.join(sorted(overlap)[:2])}"
    return 4, "farther location match"


def build_hospital_recommendations(disease, patient_location):
    seed_default_hospitals()
    hospitals = Hospital.query.order_by(Hospital.name).all()
    disease_score_field = DISEASE_SCORE_FIELDS.get(disease, "heart_score")
    specialty = SPECIALTY_MAP.get(disease, "General").lower()
    recommendations = []

    for hospital in hospitals:
        expertise_score = int(getattr(hospital, disease_score_field, 60) or 60)
        location_score, location_reason = compute_location_score(patient_location, hospital)

        specialty_bonus = 0
        hospital_specialty = (hospital.specialty or "").lower()
        if specialty in hospital_specialty:
            specialty_bonus = 12
        elif "general" in hospital_specialty or "multi" in hospital_specialty:
            specialty_bonus = 6

        recommendation_score = round((expertise_score * 0.7) + location_score + specialty_bonus, 1)
        recommendations.append({
            "hospital": hospital,
            "recommendation_score": min(99, recommendation_score),
            "expertise_score": expertise_score,
            "location_reason": location_reason,
            "city": hospital.city or "Unknown",
            "locality": hospital.locality or "Unknown"
        })

    recommendations.sort(
        key=lambda item: (
            item["recommendation_score"],
            item["expertise_score"],
            item["hospital"].name.lower()
        ),
        reverse=True
    )
    return recommendations[:5]


def init_routes(app):
    @app.route("/")
    def home():
        if session.get("user_role") == "admin":
            return redirect(url_for("admin_dashboard"))
        if session.get("user_role") == "user":
            return redirect(url_for("user_dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            if User.query.filter_by(email=email).first():
                flash("Email already registered.", "warning")
                return redirect(url_for("register"))
            user = User(name=name, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            user = User.query.filter_by(email=email, password=password).first()
            if not user:
                flash("Invalid credentials.", "danger")
                return redirect(url_for("login"))
            session["user_id"] = user.id
            session["user_role"] = "user"
            session["user_name"] = user.name
            return redirect(url_for("user_dashboard"))
        return render_template("login.html")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            admin = Admin.query.filter_by(username=username, password=password).first()
            if not admin:
                flash("Admin credentials invalid.", "danger")
                return redirect(url_for("admin_login"))
            session["user_id"] = admin.id
            session["user_role"] = "admin"
            session["user_name"] = admin.username
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/admin/dashboard")
    def admin_dashboard():
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        hospitals_count = Hospital.query.count()
        users_count = User.query.count()
        feedbacks_count = Feedback.query.count()
        return render_template("admin_dashboard.html", hospitals=hospitals_count, users=users_count, feedbacks=feedbacks_count)

    @app.route("/admin/hospitals")
    def admin_hospitals():
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        seed_default_hospitals()
        hospitals = Hospital.query.order_by(Hospital.name).all()
        return render_template("admin_hospitals.html", hospitals=hospitals)

    @app.route("/admin/hospitals/add", methods=["POST"])
    def admin_add_hospital():
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        name = request.form.get("name")
        address = request.form.get("address")
        specialty = request.form.get("specialty")
        phone = request.form.get("phone")
        description = request.form.get("description")
        city = request.form.get("city")
        locality = request.form.get("locality")
        heart_score = request.form.get("heart_score") or 60
        liver_score = request.form.get("liver_score") or 60
        diabetes_score = request.form.get("diabetes_score") or 60
        hospital = Hospital(
            name=name,
            address=address,
            specialty=specialty,
            phone=phone,
            description=description,
            city=city,
            locality=locality,
            heart_score=int(heart_score),
            liver_score=int(liver_score),
            diabetes_score=int(diabetes_score)
        )
        db.session.add(hospital)
        db.session.commit()
        flash("Hospital added successfully.", "success")
        return redirect(url_for("admin_hospitals"))

    @app.route("/admin/hospitals/edit/<int:hospital_id>", methods=["POST"])
    def admin_edit_hospital(hospital_id):
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        hospital = Hospital.query.get_or_404(hospital_id)
        hospital.name = request.form.get("name")
        hospital.address = request.form.get("address")
        hospital.specialty = request.form.get("specialty")
        hospital.phone = request.form.get("phone")
        hospital.description = request.form.get("description")
        hospital.city = request.form.get("city")
        hospital.locality = request.form.get("locality")
        hospital.heart_score = int(request.form.get("heart_score") or 60)
        hospital.liver_score = int(request.form.get("liver_score") or 60)
        hospital.diabetes_score = int(request.form.get("diabetes_score") or 60)
        db.session.commit()
        flash("Hospital updated successfully.", "success")
        return redirect(url_for("admin_hospitals"))

    @app.route("/admin/hospitals/delete/<int:hospital_id>")
    def admin_delete_hospital(hospital_id):
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        hospital = Hospital.query.get_or_404(hospital_id)
        db.session.delete(hospital)
        db.session.commit()
        flash("Hospital removed successfully.", "success")
        return redirect(url_for("admin_hospitals"))

    @app.route("/admin/users")
    def admin_users():
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        users = User.query.order_by(User.registered_at.desc()).all()
        return render_template("admin_users.html", users=users)

    @app.route("/admin/feedback")
    def admin_feedback():
        if session.get("user_role") != "admin":
            return redirect(url_for("admin_login"))
        feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
        return render_template("admin_feedback.html", feedbacks=feedbacks)

    @app.route("/user/dashboard")
    def user_dashboard():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        history = []
        if session.get("user_id"):
            history = SymptomEntry.query.filter_by(user_id=session.get("user_id")).order_by(SymptomEntry.created_at.desc()).limit(3).all()
        return render_template("user_dashboard.html", name=session.get("user_name"), history=history)

    @app.route("/user/symptoms", methods=["GET", "POST"])
    def user_symptoms():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        diagnosis = None
        history = []
        if session.get("user_id"):
            history = SymptomEntry.query.filter_by(user_id=session.get("user_id")).order_by(SymptomEntry.created_at.desc()).limit(5).all()
        if request.method == "POST":
            symptoms = request.form.get("symptoms", "").strip()
            if not symptoms:
                flash("Please describe your symptoms clearly.", "warning")
                return redirect(url_for("user_symptoms"))
            disease, confidence = analyze_symptoms(symptoms)
            prescription = None
            diagnosis_text = "Unknown"
            description = "Your symptoms did not match a clear disease category. Please try again or consult a doctor."
            if disease is not None:
                diagnosis_text = disease.title()
                description = SYMPTOM_DESCRIPTIONS.get(disease, "")
                prescription = PRESCRIPTIONS.get(disease)
                diagnosis = {
                    "disease": diagnosis_text,
                    "confidence": confidence,
                    "symptoms": symptoms,
                    "description": description,
                    "prescription": prescription
                }
            else:
                diagnosis = {
                    "disease": "Unclear",
                    "confidence": confidence,
                    "symptoms": symptoms,
                    "description": description,
                    "prescription": "Please consult a medical professional for an accurate diagnosis."
                }
            entry = SymptomEntry(
                user_id=session.get("user_id"),
                symptoms=symptoms,
                diagnosis=diagnosis_text,
                confidence=confidence,
                prescription=prescription
            )
            db.session.add(entry)
            db.session.commit()
            history = SymptomEntry.query.filter_by(user_id=session.get("user_id")).order_by(SymptomEntry.created_at.desc()).limit(5).all()
        return render_template("user_symptoms.html", diagnosis=diagnosis, history=history)

    @app.route("/user/predict", methods=["GET", "POST"])
    def user_predict():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        disease = request.args.get("disease", "heart").lower()
        if disease not in PREDICTION_FIELD_COUNTS:
            disease = "heart"
        result = None
        suggestions = []
        patient_location = request.form.get("location", "").strip() if request.method == "POST" else request.args.get("location", "").strip()
        if request.method == "POST":
            values = []
            try:
                for i in range(1, PREDICTION_FIELD_COUNTS[disease] + 1):
                    field_value = request.form.get(f"f{i}", "").strip()
                    if not field_value:
                        raise ValueError("Missing value")
                    values.append(float(field_value))
            except (ValueError, TypeError):
                flash("Please enter valid numeric values for all prediction fields.", "warning")
                return redirect(url_for("user_predict", disease=disease))
            prediction, probability = predict_disease(disease, values)
            if prediction is None:
                flash("Prediction model is unavailable. Please contact support.", "danger")
                return redirect(url_for("user_dashboard"))
            score = round(probability * 100, 1) if probability is not None else None
            message = "High risk" if prediction == 1 else "Low risk"
            result = {
                "disease": disease.title(),
                "message": message,
                "score": score,
                "values": values,
                "prescription": PRESCRIPTIONS.get(disease),
                "location": patient_location
            }
            suggestions = build_hospital_recommendations(disease, patient_location)
        help_text = VALID_HELP.get(disease, "Fill the fields accurately.")
        return render_template(
            "user_predict.html",
            disease=disease,
            help_text=help_text,
            result=result,
            suggestions=suggestions,
            patient_location=patient_location
        )

    @app.route("/user/chatbot", methods=["GET", "POST"])
    def user_chatbot():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        answer = None
        if request.method == "POST":
            prompt = (request.form.get("prompt", "") or "").lower().strip()
            if not prompt:
                answer = "I didn't catch that. Could you describe your symptoms or ask a health question?"
            else:
                disease, confidence = analyze_symptoms(prompt)
                if disease:
                    advice = CARE_ADVICE[disease]
                    answer = append_medicine_guidance(format_care_response(
                        f"I've analyzed your symptoms. It sounds like {disease.title()}-related concerns ({confidence}% confidence).",
                        SYMPTOM_DESCRIPTIONS[disease],
                        advice,
                        confidence=None
                    ), disease)
                elif any(term in prompt for term in ["hello", "hi", "hey", "who are you"]):
                    answer = "Hello! I am your OmniHealth AI assistant. I can help analyze symptoms for Heart, Liver, or Diabetes conditions. How are you feeling today?"
                elif any(term in prompt for term in ["heart", "chest pain", "blood pressure", "palpitations", "shortness of breath", "cold sweat"]):
                    advice = CARE_ADVICE["heart"]
                    answer = append_medicine_guidance(format_care_response(
                        "Heart Health Guidance",
                        "Your description suggests potential heart-related concerns. Common symptoms include chest pressure, shortness of breath, and palpitations.",
                        advice
                    ), "heart")
                elif any(term in prompt for term in ["liver", "jaundice", "abdominal pain", "bilirubin", "yellow", "dark urine"]):
                    advice = CARE_ADVICE["liver"]
                    answer = append_medicine_guidance(format_care_response(
                        "Liver Health Guidance",
                        "Your symptoms may be related to liver health. Liver issues often manifest as jaundice (yellowing skin/eyes), abdominal discomfort, or dark urine.",
                        advice
                    ), "liver")
                elif any(term in prompt for term in ["diabetes", "thirst", "urination", "glucose", "sugar", "blurred vision", "weight loss"]):
                    advice = CARE_ADVICE["diabetes"]
                    answer = append_medicine_guidance(format_care_response(
                        "Diabetes Health Guidance",
                        "These signs could be related to diabetes or high blood sugar. Typical symptoms include excessive thirst, frequent urination, and blurred vision.",
                        advice
                    ), "diabetes")
                elif any(term in prompt for term in ["prescription", "medicine", "treatment", "medication", "cure", "help"]):
                    disease_key = None
                    for key in PRESCRIPTIONS:
                        if key in prompt:
                            disease_key = key
                            break
                    if disease_key:
                        advice = CARE_ADVICE[disease_key]
                        answer = append_medicine_guidance(format_care_response(
                            f"Management for {disease_key.title()}",
                            PRESCRIPTIONS.get(disease_key),
                            advice
                        ), disease_key)
                    else:
                        answer = "I can provide general care guidance for Heart, Liver, and Diabetes. Which one would you like to know about? For example, ask 'What is the treatment for Heart concerns?'"
                elif any(term in prompt for term in ["emergency", "severe", "pain", "dying", "help me"]):
                    answer = "IMPORTANT: If you are experiencing a medical emergency, severe pain, or difficulty breathing, please call your local emergency services (like 102 or 108) or visit the nearest hospital immediately."
                else:
                    answer = "I'm sorry, I couldn't match your symptoms to my current database (Heart, Liver, or Diabetes). Could you please provide more details, or try one of our specific prediction labs?"
        return render_template("user_chatbot.html", answer=answer)

    @app.route("/user/hospitals")
    def user_hospitals():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        seed_default_hospitals()
        hospitals = Hospital.query.order_by(Hospital.name).all()
        return render_template("user_hospitals.html", hospitals=hospitals)

    @app.route("/user/feedback", methods=["GET", "POST"])
    def user_feedback():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        if request.method == "POST":
            user = User.query.get(session.get("user_id"))
            if not user:
                session.clear()
                flash("Your session expired. Please log in again.", "warning")
                return redirect(url_for("login"))
            name = session.get("user_name")
            email = user.email
            message = request.form.get("message")
            feedback = Feedback(user_name=name, email=email, message=message)
            db.session.add(feedback)
            db.session.commit()
            flash("Thank you for your feedback.", "success")
            return redirect(url_for("user_feedback"))
        return render_template("user_feedback.html")

    @app.route("/user/rnn", methods=["GET", "POST"])
    def user_rnn():
        if session.get("user_role") != "user":
            return redirect(url_for("login"))
        rnn_result = None
        if request.method == "POST":
            values = []
            try:
                for i in range(1, 6):
                    field_value = request.form.get(f"seq{i}", "").strip()
                    if not field_value:
                        raise ValueError("Missing value")
                    values.append(float(field_value))
            except (ValueError, TypeError):
                flash("Please enter valid numeric values for all RNN fields.", "warning")
                return redirect(url_for("user_rnn"))
            prediction, score = predict_rnn(values)
            rnn_result = {"prediction": "High risk" if prediction == 1 else "Low risk", "score": round(score * 100, 1)}
        return render_template("user_rnn.html", result=rnn_result)
