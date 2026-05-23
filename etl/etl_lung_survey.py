"""
ETL Pipeline pour Lung Cancer Survey Dataset
Charge les donnees de l'enquete sur le cancer du poumon
"""

import pandas as pd
import psycopg2
import pygrametl
from pygrametl.tables import CachedDimension, FactTable
import sys
import os

# Ajouter le repertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from etl.transformations import DataTransformer

def run_lung_survey_etl():
    """Pipeline ETL principal pour le dataset lung survey"""
    
    print("=== ETL Lung Cancer Survey ===")
    print("1. Connexion a la base de donnees...")
    
    # Connexion a la base de donnees
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        conn.autocommit = True
        connection = pygrametl.ConnectionWrapper(conn)
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return
    
    print("2. Chargement du dataset...")
    
    # Charger le dataset
    try:
        df = pd.read_csv(config.DATASET_LUNG_SURVEY)
        print(f"   Nombre de lignes: {len(df)}")
        print(f"   Colonnes: {list(df.columns)}")
    except Exception as e:
        print(f"Erreur de chargement du fichier: {e}")
        return
    
    print("3. Nettoyage et transformation des donnees...")
    
    # Nettoyer les noms de colonnes (enlever espaces)
    df.columns = df.columns.str.strip()
    
    # Transformer les codes binaires (1,2 -> 0,1)
    binary_cols = ['SMOKING', 'YELLOW_FINGERS', 'ANXIETY', 'PEER_PRESSURE', 
                   'CHRONIC DISEASE', 'FATIGUE', 'ALLERGY', 'WHEEZING',
                   'ALCOHOL CONSUMING', 'COUGHING', 'SHORTNESS OF BREATH',
                   'SWALLOWING DIFFICULTY', 'CHEST PAIN']
    
    transformer = DataTransformer()
    df = transformer.encode_binary_features(
        df, 
        binary_cols, 
        config.TRANSFORMATION_CONFIG['binary_encoding']
    )
    
    # Encoder LUNG_CANCER (YES/NO -> 1/0)
    df['LUNG_CANCER'] = transformer.encode_yes_no(df['LUNG_CANCER'])
    
    # Calculer les scores composites
    print("4. Calcul des scores composites...")
    
    # Score de risque
    df['risk_score'] = transformer.calculate_risk_score(
        df,
        smoking_col='SMOKING',
        chronic_col='CHRONIC DISEASE',
        alcohol_col='ALCOHOL CONSUMING',
        age_col='AGE'
    )
    
    # Score de severite des symptomes
    symptom_cols = ['YELLOW_FINGERS', 'ANXIETY', 'FATIGUE', 'ALLERGY', 
                    'WHEEZING', 'COUGHING', 'SHORTNESS OF BREATH',
                    'SWALLOWING DIFFICULTY', 'CHEST PAIN']
    df['symptom_severity'] = transformer.calculate_symptom_severity(df, symptom_cols)
    
    print("5. Definition des dimensions et tables de faits...")
    
    # Dimension: Symptomes
    dim_symptoms = CachedDimension(
        name='dim_symptoms',
        key='symptoms_id',
        attributes=['yellow_fingers', 'anxiety', 'fatigue', 'allergy', 'wheezing',
                   'coughing', 'shortness_breath', 'swallowing_difficulty', 'chest_pain'],
        targetconnection=connection
    )
    
    # Dimension: Facteurs de Risque
    dim_risk_factors = CachedDimension(
        name='dim_risk_factors',
        key='risk_factors_id',
        attributes=['smoking', 'peer_pressure', 'chronic_disease', 'alcohol_consuming'],
        targetconnection=connection
    )
    
    # Dimension: Date (recuperer l'ID par defaut)
    cursor = connection.cursor()
    cursor.execute("SELECT date_id FROM dim_date WHERE year = 2020 LIMIT 1")
    default_date_id = cursor.fetchone()[0]
    
    # Table de Faits
    fact_table = FactTable(
        name='fact_lung_survey',
        keyrefs=['symptoms_id', 'risk_factors_id', 'date_id'],
        measures=['gender', 'age', 'lung_cancer', 'risk_score', 'symptom_severity'],
        targetconnection=connection
    )
    
    print("6. Chargement des donnees...")
    
    loaded_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Dimension Symptomes
            symptoms_row = {
                'yellow_fingers': int(row['YELLOW_FINGERS']),
                'anxiety': int(row['ANXIETY']),
                'fatigue': int(row['FATIGUE']),
                'allergy': int(row['ALLERGY']),
                'wheezing': int(row['WHEEZING']),
                'coughing': int(row['COUGHING']),
                'shortness_breath': int(row['SHORTNESS OF BREATH']),
                'swallowing_difficulty': int(row['SWALLOWING DIFFICULTY']),
                'chest_pain': int(row['CHEST PAIN'])
            }
            symptoms_id = dim_symptoms.ensure(symptoms_row)
            
            # Dimension Facteurs de Risque
            risk_row = {
                'smoking': int(row['SMOKING']),
                'peer_pressure': int(row['PEER_PRESSURE']),
                'chronic_disease': int(row['CHRONIC DISEASE']),
                'alcohol_consuming': int(row['ALCOHOL CONSUMING'])
            }
            risk_id = dim_risk_factors.ensure(risk_row)
            
            # Table de Faits
            fact_row = {
                'symptoms_id': symptoms_id,
                'risk_factors_id': risk_id,
                'date_id': default_date_id,
                'gender': row['GENDER'],
                'age': int(row['AGE']),
                'lung_cancer': int(row['LUNG_CANCER']),
                'risk_score': float(row['risk_score']),
                'symptom_severity': float(row['symptom_severity'])
            }
            
            fact_table.insert(fact_row)
            loaded_count += 1
            
            if (loaded_count % 50) == 0:
                print(f"   Charge {loaded_count} lignes...")
                
        except Exception as e:
            error_count += 1
            print(f"   Erreur ligne {idx}: {e}")
    
    # Validation finale
    print("\n7. Validation et statistiques...")
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_lung_survey")
    total_loaded = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT symptoms_id) FROM dim_symptoms")
    unique_symptoms = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT risk_factors_id) FROM dim_risk_factors")
    unique_risks = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(risk_score), AVG(symptom_severity) FROM fact_lung_survey")
    avg_scores = cursor.fetchone()
    
    print(f"\n[OK] ETL Lung Survey termine avec succes!")
    print(f"  - Lignes chargees: {total_loaded}")
    print(f"  - Profils symptomatiques uniques: {unique_symptoms}")
    print(f"  - Profils de risque uniques: {unique_risks}")
    print(f"  - Score de risque moyen: {avg_scores[0]:.4f}")
    print(f"  - Severite symptomes moyenne: {avg_scores[1]:.4f}")
    print(f"  - Erreurs: {error_count}")
    
    connection.commit()
    connection.close()

if __name__ == '__main__':
    run_lung_survey_etl()
