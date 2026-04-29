import os
import shutil
from kaggle.api.kaggle_api_extended import KaggleApi

BASE_DIR = os.path.dirname(__file__)
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "omnihealth_datasets")
DATA_DIR = os.path.join(BASE_DIR, "data")

DATASETS = {
    "heart": {
        "dataset": "ronitf/heart-disease-uci",
        "file": "heart.csv",
        "dest": "heart.csv"
    },
    "diabetes": {
        "dataset": "uciml/pima-indians-diabetes-database",
        "file": "diabetes.csv",
        "dest": "diabetes.csv"
    },
    "liver": {
        "dataset": "uciml/indian-liver-patients-dataset",
        "file": "indian_liver_patient.csv",
        "dest": "liver.csv"
    }
}

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def download_datasets():
    api = KaggleApi()
    api.authenticate()

    for key, spec in DATASETS.items():
        print(f"Downloading {spec['file']} from {spec['dataset']}...")
        api.dataset_download_files(spec["dataset"], path=DOWNLOADS_DIR, unzip=True, force=True)

        source_path = os.path.join(DOWNLOADS_DIR, spec["file"])
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Downloaded file not found: {source_path}")

        dest_path = os.path.join(DATA_DIR, spec["dest"])
        shutil.copyfile(source_path, dest_path)
        print(f"Saved {spec['file']} to {source_path} and copied to {dest_path}")

    print("All datasets downloaded and copied successfully.")
    print(f"Downloads folder: {DOWNLOADS_DIR}")
    print(f"Backend data folder: {DATA_DIR}")


if __name__ == "__main__":
    download_datasets()
