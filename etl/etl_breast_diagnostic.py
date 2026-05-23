"""
ETL Pipeline pour Breast Cancer Diagnostic Dataset (Wisconsin)
Charge les mesures diagnostiques avec normalisation
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

def run_breast_diagnostic_etl():
    """Pipeline ETL principal pour le dataset breast diagnostic"""
    
    print("=== ETL Breast Cancer Diagnostic ===")
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
        df = pd.read_csv(config.DATASET_BREAST_DIAGNOSTIC)
        print(f"   Nombre de lignes: {len(df)}")
        print(f"   Colonnes: {len(df.columns)}")
    except Exception as e:
        print(f"Erreur de chargement du fichier: {e}")
        return
    
    print("3. Preparation et normalisation des donnees...")
    
    # Colonnes de mesures a normaliser
    measurement_cols = [col for col in df.columns if col not in ['id', 'diagnosis']]
    
    transformer = DataTransformer()
    
    # Normalisation MinMax des mesures
    if config.TRANSFORMATION_CONFIG['normalization_method'] == 'minmax':
        df = transformer.normalize_minmax(df, measurement_cols)
    else:
        df = transformer.normalize_standard(df, measurement_cols)
    
    print("4. Creation des features composites...")
    
    # Ajouter des features derivees
    df = transformer.create_composite_features(df)
    
    print("5. Definition des dimensions et tables de faits...")
    
    # Dimension: Mesures
    # Lister toutes les colonnes de mesures (Noms SQL avec underscores)
    measure_attributes = [
        'radius_mean', 'texture_mean', 'perimeter_mean', 'area_mean',
        'smoothness_mean', 'compactness_mean', 'concavity_mean', 
        'concave_points_mean', 'symmetry_mean', 'fractal_dimension_mean',
        'radius_se', 'texture_se', 'perimeter_se', 'area_se',
        'smoothness_se', 'compactness_se', 'concavity_se',
        'concave_points_se', 'symmetry_se', 'fractal_dimension_se',
        'radius_worst', 'texture_worst', 'perimeter_worst', 'area_worst',
        'smoothness_worst', 'compactness_worst', 'concavity_worst',
        'concave_points_worst', 'symmetry_worst', 'fractal_dimension_worst'
    ]
    
    # Ajouter les features composites si elles existent
    if 'radius_texture_ratio' in df.columns:
        measure_attributes.append('radius_texture_ratio')
    if 'area_perimeter_ratio' in df.columns:
        measure_attributes.append('area_perimeter_ratio')
    if 'worst_avg' in df.columns:
        measure_attributes.append('worst_avg')
    
    dim_measurements = CachedDimension(
        name='dim_measurements',
        key='measurements_id',
        attributes=measure_attributes,
        targetconnection=connection
    )
    
    # Recuperer les IDs des types de diagnostic
    cursor = connection.cursor()
    cursor.execute("SELECT diagnosis_type_id, diagnosis_code FROM dim_diagnosis_type")
    diagnosis_mapping = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Dimension: Date (recuperer l'ID par defaut)
    cursor.execute("SELECT date_id FROM dim_date WHERE year = 2020 LIMIT 1")
    default_date_id = cursor.fetchone()[0]
    
    # Table de Faits
    fact_table = FactTable(
        name='fact_breast_diagnostic',
        keyrefs=['measurements_id', 'diagnosis_type_id', 'date_id'],
        measures=['patient_id'],
        targetconnection=connection
    )
    
    print("6. Chargement des donnees...")
    
    loaded_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Dimension Mesures - construire le dictionnaire dynamiquement
            measurements_row = {}
            
            for attr in measure_attributes:
                # Mapping: attribut SQL (underscore) -> colonne CSV (espace ou underscore)
                col_name_csv = attr
                if attr not in df.columns:
                    # Essayer de remplacer 'concave_points' par 'concave points'
                    col_name_csv = attr.replace('concave_points', 'concave points')
                
                if col_name_csv in df.columns:
                    value = row[col_name_csv]
                    # Convertir en float et gerer les NaN
                    if pd.isna(value):
                        measurements_row[attr] = 0.0
                    else:
                        measurements_row[attr] = float(value)
                else:
                    measurements_row[attr] = 0.0
            
            measurements_id = dim_measurements.ensure(measurements_row)
            
            # Recuperer le type de diagnostic
            diagnosis_code = row['diagnosis']
            diagnosis_type_id = diagnosis_mapping.get(diagnosis_code, 1)  # Default to first type
            
            # Table de Faits
            fact_row = {
                'measurements_id': measurements_id,
                'diagnosis_type_id': diagnosis_type_id,
                'date_id': default_date_id,
                'patient_id': str(row['id'])
            }
            
            fact_table.insert(fact_row)
            loaded_count += 1
            
            if (loaded_count % 100) == 0:
                print(f"   Charge {loaded_count} lignes...")
                
        except Exception as e:
            error_count += 1
            print(f"   Erreur ligne {idx}: {e}")
    
    # Validation finale
    print("\n7. Validation et statistiques...")
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_breast_diagnostic")
    total_loaded = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT measurements_id) FROM dim_measurements")
    unique_measurements = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT dt.diagnosis_label, COUNT(*) 
        FROM fact_breast_diagnostic fbd
        JOIN dim_diagnosis_type dt ON fbd.diagnosis_type_id = dt.diagnosis_type_id
        GROUP BY dt.diagnosis_label
    """)
    diagnosis_counts = cursor.fetchall()
    
    print(f"\n[OK] ETL Breast Diagnostic termine avec succes!")
    print(f"  - Lignes chargees: {total_loaded}")
    print(f"  - Profils de mesures uniques: {unique_measurements}")
    print(f"  - Distribution des diagnostics:")
    for diag_label, count in diagnosis_counts:
        print(f"    - {diag_label}: {count}")
    print(f"  - Erreurs: {error_count}")
    
    connection.commit()
    connection.close()

if __name__ == '__main__':
    run_breast_diagnostic_etl()
