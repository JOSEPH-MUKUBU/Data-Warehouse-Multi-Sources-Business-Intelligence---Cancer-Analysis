import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def generate_dashboard():
    print("Connecting to Data Warehouse for Analysis...")
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 1. Fetch Data
    query = """
    SELECT 
        f.tumor_size, 
        f.regional_node_positive, 
        f.survival_months,
        d.t_stage, 
        d.stage_6th,
        d.grade,
        p.race, 
        p.marital_status,
        o.status
    FROM fact_breast_clinical f
    JOIN dim_diagnosis d ON f.diagnosis_id = d.diagnosis_id
    JOIN dim_patient p ON f.patient_id = p.patient_id
    JOIN dim_outcome o ON f.outcome_id = o.outcome_id
    """
    
    print("Executing query...")
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print("No data found in Data Warehouse. Run ETL first.")
        return

    # Setup styles
    sns.set(style="whitegrid")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # KPI 1: Distribution of Survival Months
    plt.figure(figsize=(10, 6))
    sns.histplot(df['survival_months'], bins=30, kde=True, color='skyblue')
    plt.title('Distribution of Survival Months')
    plt.xlabel('Months')
    plt.ylabel('Count of Patients')
    plt.savefig(os.path.join(output_dir, 'kpi_survival_dist.png'))
    print("Generated kpi_survival_dist.png")
    
    # KPI 2: Cancer Stages Count (Pie Chart)
    stage_counts = df['stage_6th'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(stage_counts, labels=stage_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    plt.title('Distribution of Cancer Stages (6th Stage)')
    plt.savefig(os.path.join(output_dir, 'kpi_stage_pie.png'))
    print("Generated kpi_stage_pie.png")

    # KPI 3: Average Tumor Size by T-Stage
    plt.figure(figsize=(10, 6))
    sns.barplot(x='t_stage', y='tumor_size', data=df, palette='viridis', ci=None)
    plt.title('Average Tumor Size by T-Stage')
    plt.xlabel('T-Stage')
    plt.ylabel('Avg Tumor Size (mm)')
    plt.savefig(os.path.join(output_dir, 'kpi_tumor_size_stage.png'))
    print("Generated kpi_tumor_size_stage.png")

    # KPI 4: Survival Status by Marital Status (Stacked Bar)
    # Pivot table for plotting
    pivot_df = df.groupby(['marital_status', 'status']).size().unstack(fill_value=0)
    pivot_df.plot(kind='bar', stacked=True, figsize=(10, 6), color=['#e74c3c', '#2ecc71'])
    plt.title('Survival Status by Marital Status')
    plt.xlabel('Marital Status')
    plt.ylabel('Number of Patients')
    plt.legend(title='Status')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'kpi_status_marital.png'))
    print("Generated kpi_status_marital.png")
    
    print("Dashboard generation complete. Images saved in 'dashboard' folder.")

if __name__ == "__main__":
    generate_dashboard()
