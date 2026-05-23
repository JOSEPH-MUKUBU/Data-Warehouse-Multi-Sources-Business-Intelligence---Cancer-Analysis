"""
Script de visualisation pour les donnees Lung Cancer Survey
Genere des visualisations avancees: matrices de correlation, radar charts, distribution des risques
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
sns.set_palette("husl")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_db_connection():
    return psycopg2.connect(**config.DB_CONFIG)

def plot_correlation_matrix(df):
    """Genere une heatmap de correlation"""
    plt.figure(figsize=(12, 10))
    
    # Calculer la correlation
    corr = df.corr()
    
    # Masquer la partie superieure
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap='coolwarm',
                vmax=1, vmin=-1, center=0, square=True, linewidths=.5)
    
    plt.title('Matrice de Correlation - Facteurs et Symptomes Lung Cancer', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'lung_correlation_matrix.png'))
    plt.close()
    print("[OK] Matrice de correlation generee")

def plot_symptom_radar(df):
    """Genere un radar chart comparant Patients Cancer vs Non-Cancer"""
    
    # Colonnes de symptomes
    symptoms = ['yellow_fingers', 'anxiety', 'fatigue', 'allergy', 'wheezing', 
                'coughing', 'shortness_breath', 'swallowing_difficulty', 'chest_pain']
    
    # Moyennes par groupe (Cancer vs No Cancer)
    means = df.groupby('lung_cancer')[symptoms].mean()
    
    # Preparation des donnees pour le radar chart
    categories = symptoms
    N = len(categories)
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += [angles[0]]  # Fermer la boucle
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Tracer pour No Cancer (0)
    values0 = means.loc[0].values.flatten().tolist()
    values0 += [values0[0]]
    ax.plot(angles, values0, linewidth=2, linestyle='solid', label='No Cancer')
    ax.fill(angles, values0, alpha=0.1)
    
    # Tracer pour Cancer (1)
    values1 = means.loc[1].values.flatten().tolist()
    values1 += [values1[0]]
    ax.plot(angles, values1, linewidth=2, linestyle='solid', label='Cancer Positive')
    ax.fill(angles, values1, alpha=0.1)
    
    # Labels
    plt.xticks(angles[:-1], categories)
    ax.set_rlabel_position(0)
    plt.yticks([0.2, 0.4, 0.6, 0.8], ["0.2", "0.4", "0.6", "0.8"], color="grey", size=7)
    plt.ylim(0, 1)
    
    plt.title('Profil Symptomatique Moyen: Cancer vs Sain', size=20, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'lung_symptom_radar.png'))
    plt.close()
    print("[OK] Radar chart genere")

def plot_risk_factors_impact(df):
    """Visualise l'impact des facteurs de risque sur le score de risque moyen"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    risk_factors = ['smoking', 'alcohol_consuming', 'chronic_disease', 'peer_pressure']
    
    for i, factor in enumerate(risk_factors):
        sns.barplot(data=df, x=factor, y='lung_cancer', ax=axes[i], palette='viridis')
        axes[i].set_title(f'Probabilite de Cancer selon {factor}')
        axes[i].set_ylabel('Taux de Cancer')
        axes[i].set_ylim(0, 1.0)
    
    plt.suptitle('Impact des Facteurs de Risque sur la Prevalence du Cancer', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'lung_risk_factors.png'))
    plt.close()
    print("[OK] Analyse des facteurs de risque generee")

def plot_demographics_distribution(df):
    """Distribution par Age et Genre"""
    plt.figure(figsize=(12, 6))
    
    sns.histplot(data=df, x='age', hue='lung_cancer', multiple='stack', bins=15, palette='Set2')
    
    plt.title('Distribution des Cas de Cancer par Age', fontsize=15)
    plt.xlabel('Age')
    plt.ylabel('Nombre de Patients')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'lung_age_distribution.png'))
    plt.close()
    print("[OK] Distribution demographique generee")

def run_viz():
    print("Generation des visualisations Lung Survey...")
    conn = get_db_connection()
    
    # Recuperer les donnees via la vue creee
    query = "SELECT * FROM v_lung_survey_summary"
    df = pd.read_sql(query, conn)
    
    # Recuperer plus de details pour la matrice de correlation
    query_full = """
    SELECT 
        ls.lung_cancer, ls.age, ls.risk_score, ls.symptom_severity,
        r.smoking, r.alcohol_consuming, r.peer_pressure, r.chronic_disease,
        s.yellow_fingers, s.anxiety, s.fatigue, s.allergy, s.wheezing,
        s.coughing, s.shortness_breath, s.swallowing_difficulty, s.chest_pain
    FROM fact_lung_survey ls
    JOIN dim_risk_factors r ON ls.risk_factors_id = r.risk_factors_id
    JOIN dim_symptoms s ON ls.symptoms_id = s.symptoms_id
    """
    df_full = pd.read_sql(query_full, conn)
    
    plot_correlation_matrix(df_full)
    plot_symptom_radar(df_full)
    plot_risk_factors_impact(df_full)
    plot_demographics_distribution(df)
    
    conn.close()
    print("Termine!")

if __name__ == '__main__':
    run_viz()
