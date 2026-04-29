# OmniHealth AI

A full-stack healthcare risk prediction project with admin and user workflows.

## Features

- Admin login and management
- Hospital CRUD operations
- User registration and login
- Heart, liver, diabetes risk prediction using Random Forest, KNN, and XGBoost
- RNN-based sequence prediction demo
- Hospital suggestions based on disease specialty
- User chatbot for model input guidance
- Feedback collection and review

## Tech stack

- Python + Flask backend
- SQLite database via SQLAlchemy
- Scikit-learn, XGBoost, TensorFlow for ML/DL
- Bootstrap 5 frontend templates

## Setup

1. Open a terminal in `omnihealthAI/backend`
2. Create a virtual environment and install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

3. Run the application:

```powershell
python app.py
```

4. Open `http://127.0.0.1:5000` in your browser.

## Default admin credentials

- Username: `admin`
- Password: `admin123`

## Dataset setup

This project can automatically download real datasets from Kaggle and save the CSV files into your Windows Downloads folder.

### Required Kaggle datasets

- Heart Disease UCI: https://www.kaggle.com/ronitf/heart-disease-uci
- Pima Indians Diabetes Database: https://www.kaggle.com/uciml/pima-indians-diabetes-database
- Indian Liver Patient Dataset: https://www.kaggle.com/uciml/indian-liver-patients-dataset

### Manual download if Kaggle API is not available

If you only have the Pima dataset right now, that is fine for diabetes prediction. For heart and liver, use one of these alternative sources and save the files into `backend/data`:

- Heart dataset: search for `heart.csv` or `heart-disease-uci.csv` from the UCI Heart Disease dataset or Kaggle link above.
- Liver dataset: look for `indian_liver_patient.csv`, `Indian Liver Patient Dataset.csv`, or `indian-liver-patient.csv`.

The app will accept any of these filenames for manual downloads:

- Heart:
  - `heart.csv`
  - `heart-disease-uci.csv`
  - `heart_disease_uci.csv`
  - `heart disease.csv`
- Liver:
  - `liver.csv`
  - `indian_liver_patient.csv`
  - `indian_liver_patient_dataset.csv`
  - `indian-liver-patient.csv`
  - `indian liver patient.csv`
  - `indian_liver_patients.csv`
- Diabetes:
  - `diabetes.csv`
  - `pima-indians-diabetes.csv`
  - `pima_indians_diabetes.csv`

### How to download the datasets automatically

1. Make sure you have a Kaggle account and `kaggle.json` credentials in `%USERPROFILE%\.kaggle\kaggle.json`.
2. Run this from the backend folder:

```powershell
cd c:\Users\ASUS\OneDrive\Desktop\omnihealthAI\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python download_datasets.py
```

The script will:

- download files into `C:\Users\ASUS\Downloads\omnihealth_datasets`
- copy the CSV files into `backend/data`

### What files are created

- `C:\Users\ASUS\Downloads\omnihealth_datasets\heart.csv` or an alternate heart file name
- `C:\Users\ASUS\Downloads\omnihealth_datasets\diabetes.csv`
- `C:\Users\ASUS\Downloads\omnihealth_datasets\indian_liver_patient.csv`

If the CSV files are not present, the app will still run using fallback synthetic data, but real dataset training is recommended for better predictions.

## Notes

- Models are cached in `backend/saved_models` so the app starts faster after the first training run.
- Add hospitals in the admin panel to enable user hospital suggestions.
