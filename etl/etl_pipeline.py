import pandas as pd
import psycopg2
import pygrametl
from pygrametl.tables import CachedDimension, FactTable
from datetime import date
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def run_etl():
    print("Starting ETL Process...")
    
    # 1. Database Connection
    try:
        connection = psycopg2.connect(**config.DB_CONFIG)
        connection.autocommit = True
        # Wrap the connection for pygrametl
        connection = pygrametl.ConnectionWrapper(connection)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure you have created the database and updated config.py")
        return

    # 2. Initialize Schema (Optional: Reset DB)
    # Note: In a production run, you might not want to always drop tables.
    # Here we reset to ensure clean state for the project.
    # 2. Initialize Schema (Optional: Reset DB)
    # Note: Handled by etl_master.py now.
    # print("Initializing Schema...")
    # try:
    #     cursor = connection.cursor()
    #     schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql', 'schema.sql')
    #     with open(schema_path, 'r') as f:
    #         cursor.execute(f.read())
    # except Exception as e:
    #     print(f"Error executing schema SQL: {e}")
    #     return

    # 3. Define Dimensions
    # We use CachedDimension for performance on small datasets
    dim_patient = CachedDimension(
        name='dim_patient',
        key='patient_id',
        attributes=['age', 'race', 'marital_status'],
        targetconnection=connection
    )

    dim_diagnosis = CachedDimension(
        name='dim_diagnosis',
        key='diagnosis_id',
        attributes=['t_stage', 'n_stage', 'stage_6th', 'differentiation', 
                    'grade', 'a_stage', 'estrogen_status', 'progesterone_status'],
        targetconnection=connection
    )

    dim_outcome = CachedDimension(
        name='dim_outcome',
        key='outcome_id',
        attributes=['status'],
        targetconnection=connection
    )

    dim_date = CachedDimension(
        name='dim_date',
        key='date_id',
        attributes=['full_date', 'year', 'month', 'quarter'],
        targetconnection=connection
    )

    # 4. Define Fact Table
    # 4. Define Fact Table
    fact_table = FactTable(
        name='fact_breast_clinical',
        keyrefs=['patient_id', 'diagnosis_id', 'outcome_id', 'date_id'],
        measures=['tumor_size', 'regional_node_examined', 'regional_node_positive', 'survival_months'],
        targetconnection=connection
    )

    # 5. Load Data
    print(f"Reading dataset from {config.DATASET_PATH}...")
    try:
        df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config.DATASET_PATH))
    except FileNotFoundError:
        print("Dataset not found! Please check config.py and file location.")
        return

    # 6. Extract & Load Loop
    print("Loading data into Data Warehouse...")
    
    # Pre-populate a default date for this analysis (Simulation)
    # In a real scenario, you'd extract a date from the row.
    today = date.today()
    dim_date.insert(
        {'full_date': today, 'year': today.year, 'month': today.month, 'quarter': (today.month-1)//3 + 1}
    )
    # We need to fetch the ID of this date to use for facts
    # Since we just inserted it and it's cached, we can look it up.
    # Actually pygrametl lookup usually matches by attributes.
    date_lookup = {'full_date': today, 'year': today.year, 'month': today.month, 'quarter': (today.month-1)//3 + 1}
    # However, 'date_id' is auto-generated in DB, CachedDimension might handle it if we return it?
    # pygrametl maps row keys. We need to ensure we pass the attributes to fact generation.
    
    row_count = 0
    
    for index, row in df.iterrows():
        # Mapping CSV columns to our Dimension attributes
        
        # Patient
        patient_row = {
            'age': row['Age'],
            'race': row['Race'].strip(),
            'marital_status': row['Marital Status'].strip()
        }
        # Insert/Lookup returns the Dimension Key ID (if configured) or updates the dict with the key
        patient_row['patient_id'] = dim_patient.ensure(patient_row) 

        # Diagnosis
        diagnosis_row = {
            't_stage': row['T Stage '].strip(), # Note the space in CSV header
            'n_stage': row['N Stage'].strip(),
            'stage_6th': row['6th Stage'].strip(),
            'differentiation': row['differentiate'].strip(),
            'grade': row['Grade'].strip(),
            'a_stage': row['A Stage'].strip(),
            'estrogen_status': row['Estrogen Status'].strip(),
            'progesterone_status': row['Progesterone Status'].strip()
        }
        diagnosis_row['diagnosis_id'] = dim_diagnosis.ensure(diagnosis_row)

        # Outcome
        outcome_row = {
            'status': row['Status'].strip()
        }
        outcome_row['outcome_id'] = dim_outcome.ensure(outcome_row)

        # Date (Default)
        # We use the same dict we used to insert earlier to ensure we get the key
        # dim_date.ensure(date_lookup) -> will popluate date_lookup['date_id']
        date_lookup['date_id'] = dim_date.ensure(date_lookup)

        # Fact
        fact_row = {
            'patient_id': patient_row['patient_id'],
            'diagnosis_id': diagnosis_row['diagnosis_id'],
            'outcome_id': outcome_row['outcome_id'],
            'date_id': date_lookup['date_id'],
            'tumor_size': row['Tumor Size'],
            'regional_node_examined': row['Regional Node Examined'],
            'regional_node_positive': row['Reginol Node Positive'],
            'survival_months': row['Survival Months']
        }
        
        fact_table.insert(fact_row)
        row_count += 1
        
        if row_count % 500 == 0:
            print(f"Processed {row_count} rows...")

    connection.commit()
    connection.close()
    print(f"ETL Completed Successfully! Total rows: {row_count}")

if __name__ == "__main__":
    run_etl()
