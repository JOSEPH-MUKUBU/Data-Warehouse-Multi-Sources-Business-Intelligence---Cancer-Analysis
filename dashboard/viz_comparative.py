"""
Script de visualisation comparative Multi-Sources
Analyse croisee entre les differents datasets de cancer
"""

import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import sys

# Configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Configuration du style
plt.style.use('seaborn-v0_8-whitegrid')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_db_connection():
    return psycopg2.connect(**config.DB_CONFIG)

def plot_age_distribution_comparison(conn):
    """Compare la distribution des ages entre Breast Clinical et Lung Survey"""
    
    # Recuperer Breast Clinical Ages
    df_breast = pd.read_sql("""
        SELECT p.age, 'Breast Cancer' as dataset
        FROM fact_breast_clinical f 
        JOIN dim_patient p ON f.patient_id = p.patient_id
    """, conn)
    
    # Recuperer Lung Survey Ages
    df_lung = pd.read_sql("""
        SELECT age, 'Lung Survey' as dataset
        FROM fact_lung_survey
    """, conn)
    
    # Combiner
    df_combined = pd.concat([df_breast, df_lung])
    
    plt.figure(figsize=(10, 6))
    sns.kdeplot(data=df_combined, x='age', hue='dataset', fill=True, common_norm=False, palette='viridis')
    
    plt.title('Comparaison des Distributions d\'Age', fontsize=16)
    plt.xlabel('Age')
    plt.ylabel('Densite')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'comparative_age_density.png'))
    plt.close()
    print("[OK] Comparaison d'age generee")

def plot_diagnosis_prevalence(conn):
    """Compare les taux de positivite/malignite entre les datasets"""
    
    # Breast Diag Malignancy Rate
    breast_diag = pd.read_sql("""
        SELECT dt.diagnosis_label as status
        FROM fact_breast_diagnostic f
        JOIN dim_diagnosis_type dt ON f.diagnosis_type_id = dt.diagnosis_type_id
    """, conn)
    breast_rate = (breast_diag['status'] == 'Malignant').mean() * 100
    
    # Lung Cancer Rate
    lung_diag = pd.read_sql("SELECT lung_cancer FROM fact_lung_survey", conn)
    lung_rate = (lung_diag['lung_cancer'] == 1).mean() * 100
    
    # Breast Clinical Survival Rate (Proxy for severity/outcome)
    breast_clin = pd.read_sql("""
        SELECT o.status 
        FROM fact_breast_clinical f
        JOIN dim_outcome o ON f.outcome_id = o.outcome_id
    """, conn)
    # Dans ce dataset 'Dead' peut etre un indicateur de resultat grave
    mortality_rate = (breast_clin['status'] == 'Dead').mean() * 100
    
    # Plot
    rates = [breast_rate, lung_rate, mortality_rate]
    labels = ['Breast Diag\n(Malignancy)', 'Lung Survey\n(Positive)', 'Breast Clinical\n(Mortality)']
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, rates, color=colors)
    
    plt.ylabel('Pourcentage (%)')
    plt.title('Comparaison des Taux de Prevalence et Severite', fontsize=16)
    plt.ylim(0, 100)
    
    # Ajouter les valeurs
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                 f'{height:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'comparative_prevalence.png'))
    plt.close()
    print("[OK] Comparaison prevalence generee")

def run_compare_viz():
    print("Generation des visualisations comparatives...")
    try:
        conn = get_db_connection()
        
        plot_age_distribution_comparison(conn)
        plot_diagnosis_prevalence(conn)
        
        conn.close()
    except Exception as e:
        print(f"Erreur lors de la generation comparative: {e}")
    print("Termine!")

if __name__ == '__main__':
    run_compare_viz()
