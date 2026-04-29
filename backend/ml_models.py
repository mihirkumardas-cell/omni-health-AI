import os
import numpy as np
import pandas as pd

try:
    import joblib
except ImportError:
    joblib = None

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "omnihealth_datasets")
MODEL_DIR = os.path.join(BASE_DIR, "saved_models")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

DATA_FILE_CANDIDATES = {
    "heart": [
        "heart.csv",
        "heart-disease-uci.csv",
        "heart_disease_uci.csv",
        "heart disease.csv",
        "heart-disease-uci-dataset.csv",
        "heart-disease-uci-dataset"
    ],
    "liver": [
        "liver.csv",
        "indian_liver_patient.csv",
        "indian_liver_patient_dataset.csv",
        "indian-liver-patient.csv",
        "indian-liver-patient-dataset.csv",
        "indian liver patient.csv",
        "indian_liver_patients.csv"
    ],
    "diabetes": [
        "diabetes.csv",
        "diabetes_data.csv",
        "pima-indians-diabetes.csv",
        "pima_indians_diabetes.csv"
    ]
}


def _resolve_possible_file(filename):
    for base_dir in (DATA_DIR, DOWNLOADS_DIR):
        candidate = os.path.join(base_dir, filename)
        if os.path.exists(candidate):
            return candidate
        if not candidate.lower().endswith(".csv"):
            alternate = candidate + ".csv"
            if os.path.exists(alternate):
                return alternate
    return None


def get_dataset_path(name):
    for file_name in DATA_FILE_CANDIDATES.get(name, []):
        resolved = _resolve_possible_file(file_name)
        if resolved:
            return resolved
    for file_name in DATA_FILE_CANDIDATES.get(name, []):
        resolved = _resolve_possible_file(file_name)
        if resolved:
            return resolved
    return os.path.join(DATA_DIR, DATA_FILE_CANDIDATES[name][0])


class DiseaseModel:
    def __init__(self, classifier, feature_count, name):
        self.classifier = classifier
        self.feature_count = feature_count
        self.name = name

    def predict(self, values):
        values = np.array(values, dtype=float).reshape(1, -1)
        prediction = self.classifier.predict(values)
        probability = self.classifier.predict_proba(values)[0][1] if hasattr(self.classifier, "predict_proba") else None
        return int(prediction[0]), float(probability) if probability is not None else None


class RNNModel:
    def __init__(self):
        self.model = None
        self.sequence_length = 5
        self.initialized = False

    def _build_model(self):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Input, LSTM, Dense
        from tensorflow.keras.optimizers import Adam

        model = Sequential([
            Input(shape=(self.sequence_length, 1)),
            LSTM(32, activation="tanh"),
            Dense(16, activation="relu"),
            Dense(1, activation="sigmoid")
        ])
        model.compile(optimizer=Adam(learning_rate=0.01), loss="binary_crossentropy", metrics=["accuracy"])
        return model

    def train(self):
        rng = np.random.RandomState(42)
        X = rng.rand(600, self.sequence_length, 1)
        y = rng.randint(0, 2, 600)
        self.model = self._build_model()
        self.model.fit(X, y, epochs=5, batch_size=32, verbose=0)

    def load_or_train(self):
        from tensorflow.keras.models import load_model

        model_path = os.path.join(MODEL_DIR, "rnn_model.h5")
        if os.path.exists(model_path):
            self.model = load_model(model_path)
            self.initialized = True
            return
        self.train()
        self.model.save(model_path)
        self.initialized = True

    def predict(self, values):
        if not self.initialized:
            self.load_or_train()
        values = np.array(values, dtype=float).reshape(1, self.sequence_length, 1)
        score = float(self.model.predict(values, verbose=0)[0][0])
        return 1 if score >= 0.5 else 0, score


def read_csv(path):
    try:
        if path and os.path.exists(path):
            return pd.read_csv(path)
        if path and not path.lower().endswith(".csv"):
            alternate = path + ".csv"
            if os.path.exists(alternate):
                return pd.read_csv(alternate)
    except Exception:
        return None
    return None


def prepare_heart_data(df):
    expected = ["age", "sex", "trestbps", "chol", "fbs", "thalach", "oldpeak", "target"]
    if not all(col in df.columns for col in expected):
        return None, None
    df = df.dropna(subset=expected)
    X = df[["age", "sex", "trestbps", "chol", "fbs", "thalach", "oldpeak"]].astype(float)
    y = (df["target"] > 0).astype(int)
    return X, y


def prepare_liver_data(df):
    expected = ["Age", "Total_Bilirubin", "Direct_Bilirubin", "Alkaline_Phosphotase", "Albumin", "Total_Protiens", "Dataset"]
    if not all(col in df.columns for col in expected):
        return None, None
    df = df.dropna(subset=expected)
    X = df[["Age", "Total_Bilirubin", "Direct_Bilirubin", "Alkaline_Phosphotase", "Albumin", "Total_Protiens"]].astype(float)
    y = (df["Dataset"] == 1).astype(int)
    return X, y


def prepare_diabetes_data(df):
    expected = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "Outcome"]
    if not all(col in df.columns for col in expected):
        return None, None
    df = df.dropna(subset=expected)
    X = df[["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]].astype(float)
    y = df["Outcome"].astype(int)
    return X, y


def fallback_data(feature_count):
    rng = np.random.RandomState(1)
    X = rng.rand(1000, feature_count) * 100
    y = rng.randint(0, 2, 1000)
    return X, y


def load_dataset(name):
    df = read_csv(get_dataset_path(name))
    if df is None:
        return None, None
    if name == "heart":
        return prepare_heart_data(df)
    if name == "liver":
        return prepare_liver_data(df)
    if name == "diabetes":
        return prepare_diabetes_data(df)
    return None, None


def load_or_train_classifier(name, classifier, feature_count):
    if joblib is None:
        raise ImportError("joblib is required to load and save trained models. Install it with 'pip install joblib'.")

    model_path = os.path.join(MODEL_DIR, f"{name}_model.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)

    X, y = load_dataset(name)
    if X is None or len(X) < 10:
        X, y = fallback_data(feature_count)

    classifier.fit(X, y)
    joblib.dump(classifier, model_path)
    return classifier


class HealthPredictors:
    def __init__(self):
        self.heart = None
        self.liver = None
        self.diabetes = None
        self.rnn = RNNModel()
        self.classifiers_initialized = False

    def initialize_classifiers(self):
        if self.classifiers_initialized:
            return
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.neighbors import KNeighborsClassifier
        except ImportError as exc:
            raise ImportError("scikit-learn is required for disease prediction. Install it with 'pip install scikit-learn'.") from exc

        self.heart = DiseaseModel(load_or_train_classifier("heart", RandomForestClassifier(n_estimators=80, random_state=5), 7), 7, "Heart")
        self.liver = DiseaseModel(load_or_train_classifier("liver", KNeighborsClassifier(n_neighbors=7), 6), 6, "Liver")

        try:
            from xgboost import XGBClassifier
            diabetes_classifier = XGBClassifier(eval_metric="logloss")
        except ImportError:
            diabetes_classifier = RandomForestClassifier(n_estimators=80, random_state=7)

        self.diabetes = DiseaseModel(load_or_train_classifier("diabetes", diabetes_classifier, 6), 6, "Diabetes")
        self.classifiers_initialized = True

    def initialize_rnn(self):
        if self.rnn.initialized:
            return
        self.rnn.load_or_train()

    def predict(self, disease, values):
        self.initialize_classifiers()
        if disease == "heart":
            return self.heart.predict(values)
        if disease == "liver":
            return self.liver.predict(values)
        if disease == "diabetes":
            return self.diabetes.predict(values)
        return None, None


predictors = HealthPredictors()


def initialize_models():
    # kept for compatibility; models will initialize lazily on demand.
    return


def predict_disease(disease, values):
    return predictors.predict(disease, values)


def predict_rnn(values):
    return predictors.rnn.predict(values)
