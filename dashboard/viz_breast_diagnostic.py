"""
Script de visualisation pour les donnees Breast Cancer Diagnostic (Wisconsin)
Genere des visualisations avancees: PCA, Boxplots comparatifs, Scatter Matrix
"""

import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
import sys

# Configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Configuration du style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_db_connection():
    return psycopg2.connect(**config.DB_CONFIG)

def plot_pca_analysis(df, features):
    """Effectue une PCA et visualise les 2 premieres composantes"""
    
    # Separer features et target
    X = df[features]
    y = df['diagnosis_label']
    
    # Standardiser (meme si deja fait dans l'ETL, PCA requiert centrage)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA
    pca = PCA(n_components=2)
    principal_components = pca.fit_transform(X_scaled)
    pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'])
    pca_df['Diagnosis'] = y
    
    # Plot
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x='PC1', y='PC2', hue='Diagnosis', data=pca_df, alpha=0.7, s=60)
    
    explained_variance = pca.explained_variance_ratio_
    plt.title(f'PCA - Breast Cancer Diagnostic\nVar Expliquee: PC1 ({explained_variance[0]:.2%}), PC2 ({explained_variance[1]:.2%})', fontsize=15)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'breast_pca_analysis.png'))
    plt.close()
    print("[OK] Analyse PCA generee")

def plot_feature_boxplots(df):
    """Boxplots comparatifs (Malignant vs Benign) pour les mesures cles"""
    
    key_features = ['radius_mean', 'texture_mean', 'area_mean', 'concavity_mean']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for i, feature in enumerate(key_features):
        sns.boxplot(x='diagnosis_label', y=feature, data=df, ax=axes[i], palette='Set3')
        axes[i].set_title(f'Distribution: {feature}')
        axes[i].set_xlabel('')
    
    plt.suptitle('Comparaison Malignant vs Benign - Mesures Cles', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'breast_boxplots.png'))
    plt.close()
    print("[OK] Boxplots comparatifs generes")

def plot_scatter_matrix(df):
    """Matrice de dispersion pour les 3 dimensions principales (mean, se, worst) du rayon"""
    
    cols = ['radius_mean', 'radius_se', 'radius_worst', 'diagnosis_label']
    
    sns.pairplot(df[cols], hue='diagnosis_label', corner=True, height=3)
    
    plt.suptitle('Relation entre les mesures de Rayon (Mean, SE, Worst)', y=1.02, fontsize=16)
    plt.savefig(os.path.join(OUTPUT_DIR, 'breast_scatter_matrix.png'))
    plt.close()
    print("[OK] Scatter matrix generee")

def plot_violin_distribution(df):
    """Violin plot pour visualiser la distribution detaillee"""
    
    # Normaliser pour affichage sur meme echelle (si non deja fait ou pour reassurance)
    data_norm = df.copy()
    features = ['smoothness_mean', 'compactness_mean', 'concavity_mean', 'symmetry_mean']
    
    # Transformer en format long pour seaborn
    df_melted = pd.melt(data_norm, id_vars=['diagnosis_label'], value_vars=features, 
                        var_name='Measurement', value_name='Value')
    
    plt.figure(figsize=(12, 6))
    sns.violinplot(x='Measurement', y='Value', hue='diagnosis_label', 
                   data=df_melted, split=True, inner='quart')
    
    plt.title('Distribution des Caracteristiques Morphologiques', fontsize=15)
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'breast_violin_features.png'))
    plt.close()
    print("[OK] Violin plots generes")

def run_viz():
    print("Generation des visualisations Breast Diagnostic...")
    conn = get_db_connection()
    
    # Recuperer toutes les donnees necessaires
    query = """
    SELECT 
        dt.diagnosis_label,
        m.*
    FROM fact_breast_diagnostic bd
    JOIN dim_diagnosis_type dt ON bd.diagnosis_type_id = dt.diagnosis_type_id
    JOIN dim_measurements m ON bd.measurements_id = m.measurements_id
    """
    df = pd.read_sql(query, conn)
    
    # Identifier les colonnes de features (tout sauf ID et label)
    features = [col for col in df.columns if col not in ['diagnosis_label', 'measurements_id']]
    
    plot_pca_analysis(df, features)
    plot_feature_boxplots(df)
    plot_scatter_matrix(df)
    plot_violin_distribution(df)
    
    conn.close()
    print("Termine!")

if __name__ == '__main__':
    run_viz()
