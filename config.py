# Configuration du Data Warehouse
import os

# Configuration de la base de donnees PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'Delta2003#',
    'dbname': 'cancer_dwh'
}

# Chemins vers les datasets
BASE_DIR = os.path.dirname(__file__)
DATASET_BREAST_CLINICAL = os.path.join(BASE_DIR, 'Breast_Cancer.csv')
DATASET_LUNG_SURVEY = os.path.join(BASE_DIR, 'survey lung cancer.csv')
DATASET_BREAST_DIAGNOSTIC = os.path.join(BASE_DIR, 'Cancer_Data.csv')

# Configuration des transformations
TRANSFORMATION_CONFIG = {
    'age_bins': [0, 30, 40, 50, 60, 70, 100],
    'age_labels': ['20-30', '31-40', '41-50', '51-60', '61-70', '70+'],
    'normalization_method': 'minmax',  # 'minmax' or 'standard'
    'binary_encoding': {1: 0, 2: 1}  # Survey encoding: 1=No, 2=Yes
}

# Mapping des colonnes pour survey lung cancer
LUNG_SURVEY_COLUMNS = {
    'GENDER': 'gender',
    'AGE': 'age',
    'SMOKING': 'smoking',
    'YELLOW_FINGERS': 'yellow_fingers',
    'ANXIETY': 'anxiety',
    'PEER_PRESSURE': 'peer_pressure',
    'CHRONIC DISEASE': 'chronic_disease',
    'FATIGUE ': 'fatigue',
    'ALLERGY ': 'allergy',
    'WHEEZING': 'wheezing',
    'ALCOHOL CONSUMING': 'alcohol_consuming',
    'COUGHING': 'coughing',
    'SHORTNESS OF BREATH': 'shortness_breath',
    'SWALLOWING DIFFICULTY': 'swallowing_difficulty',
    'CHEST PAIN': 'chest_pain',
    'LUNG_CANCER': 'lung_cancer'
}

# Legacy path for backward compatibility
DATASET_PATH = DATASET_BREAST_CLINICAL
