"""
Script principal d'orchestration ETL.
Coordonne l'execution de tous les pipelines ETL :
1. Initialisation du Schema
2. Chargement Donnees CLINIQUES (Sein)
3. Chargement Donnees ENQUETE (Poumon)
4. Chargement Donnees DIAGNOSTIC (Sein)
"""

import psycopg2
import sys
import os
from datetime import datetime

# Ajouter le repertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def init_schema():
    """Initialise le schema de la base de donnees"""
    print("=" * 60)
    print("INITIALISATION DU SCHEMA")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        cursor = conn.cursor()
        
        # Lire et executer le script SQL
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'sql',
            'schema.sql'
        )
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("[OK] Schema cree avec succes!\n")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'initialisation du schema: {e}\n")
        return False


def run_complete_etl():
    """Execute tous les pipelines ETL dans le bon ordre"""
    
    print("\n" + "=" * 60)
    print("ETL MASTER - Data Warehouse Multi-Sources")
    print("=" * 60)
    start_time = datetime.now()
    
    # Etape 1: Initialiser le schema
    if not init_schema():
        print("Echec de l'initialisation du schema. Arret de l'ETL.")
        return
    
    # Importer les modules ETL
    try:
        from etl_pipeline import run_etl as run_breast_clinical_etl
        from etl_lung_survey import run_lung_survey_etl
        from etl_breast_diagnostic import run_breast_diagnostic_etl
    except ImportError as e:
        print(f"Erreur d'importation des modules ETL: {e}")
        return
    
    results = {
        'breast_clinical': False,
        'lung_survey': False,
        'breast_diagnostic': False
    }
    
    # Etape 2: ETL Breast Clinical
    print("\n" + "=" * 60)
    print("ETAPE 2/4: Breast Cancer Clinical Data")
    print("=" * 60)
    try:
        run_breast_clinical_etl()
        results['breast_clinical'] = True
    except Exception as e:
        print(f"[ERREUR] Erreur ETL Breast Clinical: {e}")
    
    # Etape 3: ETL Lung Survey
    print("\n" + "=" * 60)
    print("ETAPE 3/4: Lung Cancer Survey Data")
    print("=" * 60)
    try:
        run_lung_survey_etl()
        results['lung_survey'] = True
    except Exception as e:
        print(f"[ERREUR] Erreur ETL Lung Survey: {e}")
    
    # Etape 4: ETL Breast Diagnostic
    print("\n" + "=" * 60)
    print("ETAPE 4/4: Breast Cancer Diagnostic Data")
    print("=" * 60)
    try:
        run_breast_diagnostic_etl()
        results['breast_diagnostic'] = True
    except Exception as e:
        print(f"[ERREUR] Erreur ETL Breast Diagnostic: {e}")
    
    # Rapport final
    print("\n" + "=" * 60)
    print("RAPPORT FINAL")
    print("=" * 60)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\nDuree totale: {duration:.2f} secondes\n")
    print("Statut des pipelines:")
    print(f"  Breast Clinical:   {'[OK] Succes' if results['breast_clinical'] else '[X] Echec'}")
    print(f"  Lung Survey:       {'[OK] Succes' if results['lung_survey'] else '[X] Echec'}")
    print(f"  Breast Diagnostic: {'[OK] Succes' if results['breast_diagnostic'] else '[X] Echec'}")
    
    # Statistiques globales
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM fact_breast_clinical")
        bc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fact_lung_survey")
        ls_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fact_breast_diagnostic")
        bd_count = cursor.fetchone()[0]
        
        total_count = bc_count + ls_count + bd_count
        
        print(f"\nLignes chargees:")
        print(f"  Breast Clinical:   {bc_count:,}")
        print(f"  Lung Survey:       {ls_count:,}")
        print(f"  Breast Diagnostic: {bd_count:,}")
        print(f"  TOTAL:             {total_count:,}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nImpossible de recuperer les statistiques: {e}")
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n{'[OK]' if success_count == 3 else '[X]'} {success_count}/3 pipelines executes avec succes")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    run_complete_etl()
