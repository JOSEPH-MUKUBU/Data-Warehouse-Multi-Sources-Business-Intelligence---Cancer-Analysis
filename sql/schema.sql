-- =============================================
-- Data Warehouse Schema - Architecture en Constellation
-- Projet: Analyse Multi-Sources du Cancer
-- =============================================

-- Suppression des tables existantes
DROP TABLE IF EXISTS fact_breast_diagnostic CASCADE;
DROP TABLE IF EXISTS fact_lung_survey CASCADE;
DROP TABLE IF EXISTS fact_breast_clinical CASCADE;
DROP TABLE IF EXISTS dim_measurements CASCADE;
DROP TABLE IF EXISTS dim_diagnosis_type CASCADE;
DROP TABLE IF EXISTS dim_symptoms CASCADE;
DROP TABLE IF EXISTS dim_risk_factors CASCADE;
DROP TABLE IF EXISTS dim_patient CASCADE;
DROP TABLE IF EXISTS dim_diagnosis CASCADE;
DROP TABLE IF EXISTS dim_outcome CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- =============================================
-- DIMENSIONS PARTAGEES
-- =============================================

-- Table de dimension: Date (partagee par toutes les faits)
CREATE TABLE dim_date (
    date_id SERIAL PRIMARY KEY,
    full_date DATE,
    year INT,
    month INT,
    quarter INT
);

-- =============================================
-- BREAST CLINICAL (Dataset original)
-- =============================================

-- Dimension: Patient (Breast Clinical)
CREATE TABLE dim_patient (
    patient_id SERIAL PRIMARY KEY,
    age INT,
    race VARCHAR(50),
    marital_status VARCHAR(50)
);

-- Dimension: Diagnosis (Breast Clinical)
CREATE TABLE dim_diagnosis (
    diagnosis_id SERIAL PRIMARY KEY,
    t_stage VARCHAR(10),
    n_stage VARCHAR(10),
    stage_6th VARCHAR(10),
    differentiation VARCHAR(100),
    grade VARCHAR(50),
    a_stage VARCHAR(50),
    estrogen_status VARCHAR(20),
    progesterone_status VARCHAR(20)
);

-- Dimension: Outcome (Breast Clinical)
CREATE TABLE dim_outcome (
    outcome_id SERIAL PRIMARY KEY,
    status VARCHAR(20)
);

-- Table de Faits: Breast Clinical
CREATE TABLE fact_breast_clinical (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES dim_patient(patient_id),
    diagnosis_id INT REFERENCES dim_diagnosis(diagnosis_id),
    outcome_id INT REFERENCES dim_outcome(outcome_id),
    date_id INT REFERENCES dim_date(date_id),
    tumor_size INT,
    regional_node_examined INT,
    regional_node_positive INT,
    survival_months INT
);

-- =============================================
-- LUNG SURVEY
-- =============================================

-- Dimension: Symptomes
CREATE TABLE dim_symptoms (
    symptoms_id SERIAL PRIMARY KEY,
    yellow_fingers INT,        -- 0=No, 1=Yes
    anxiety INT,               -- 0=No, 1=Yes
    fatigue INT,               -- 0=No, 1=Yes
    allergy INT,               -- 0=No, 1=Yes
    wheezing INT,              -- 0=No, 1=Yes
    coughing INT,              -- 0=No, 1=Yes
    shortness_breath INT,      -- 0=No, 1=Yes
    swallowing_difficulty INT, -- 0=No, 1=Yes
    chest_pain INT             -- 0=No, 1=Yes
);

-- Dimension: Facteurs de Risque
CREATE TABLE dim_risk_factors (
    risk_factors_id SERIAL PRIMARY KEY,
    smoking INT,              -- 0=No, 1=Yes
    peer_pressure INT,        -- 0=No, 1=Yes
    chronic_disease INT,      -- 0=No, 1=Yes
    alcohol_consuming INT     -- 0=No, 1=Yes
);

-- Table de Faits: Lung Survey
CREATE TABLE fact_lung_survey (
    id SERIAL PRIMARY KEY,
    gender VARCHAR(1),        -- M ou F
    age INT,
    symptoms_id INT REFERENCES dim_symptoms(symptoms_id),
    risk_factors_id INT REFERENCES dim_risk_factors(risk_factors_id),
    date_id INT REFERENCES dim_date(date_id),
    lung_cancer INT,          -- 0=No, 1=Yes
    risk_score DECIMAL(5,4),  -- Score composite calcule
    symptom_severity DECIMAL(5,4) -- Severite des symptomes
);

-- =============================================
-- BREAST DIAGNOSTIC (Wisconsin Dataset)
-- =============================================

-- Dimension: Type de Diagnostic
CREATE TABLE dim_diagnosis_type (
    diagnosis_type_id SERIAL PRIMARY KEY,
    diagnosis_code VARCHAR(1),    -- M ou B
    diagnosis_label VARCHAR(20)   -- Malignant ou Benign
);

-- Dimension: Mesures Diagnostiques (30 mesures)
CREATE TABLE dim_measurements (
    measurements_id SERIAL PRIMARY KEY,
    -- Mesures moyennes
    radius_mean DECIMAL(10,6),
    texture_mean DECIMAL(10,6),
    perimeter_mean DECIMAL(10,6),
    area_mean DECIMAL(10,6),
    smoothness_mean DECIMAL(10,6),
    compactness_mean DECIMAL(10,6),
    concavity_mean DECIMAL(10,6),
    concave_points_mean DECIMAL(10,6),
    symmetry_mean DECIMAL(10,6),
    fractal_dimension_mean DECIMAL(10,6),
    -- Erreurs standard
    radius_se DECIMAL(10,6),
    texture_se DECIMAL(10,6),
    perimeter_se DECIMAL(10,6),
    area_se DECIMAL(10,6),
    smoothness_se DECIMAL(10,6),
    compactness_se DECIMAL(10,6),
    concavity_se DECIMAL(10,6),
    concave_points_se DECIMAL(10,6),
    symmetry_se DECIMAL(10,6),
    fractal_dimension_se DECIMAL(10,6),
    -- Pires valeurs
    radius_worst DECIMAL(10,6),
    texture_worst DECIMAL(10,6),
    perimeter_worst DECIMAL(10,6),
    area_worst DECIMAL(10,6),
    smoothness_worst DECIMAL(10,6),
    compactness_worst DECIMAL(10,6),
    concavity_worst DECIMAL(10,6),
    concave_points_worst DECIMAL(10,6),
    symmetry_worst DECIMAL(10,6),
    fractal_dimension_worst DECIMAL(10,6),
    -- Features derivees
    radius_texture_ratio DECIMAL(10,6),
    area_perimeter_ratio DECIMAL(10,6),
    worst_avg DECIMAL(10,6)
);

-- Table de Faits: Breast Diagnostic
CREATE TABLE fact_breast_diagnostic (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20),           -- ID original du dataset
    measurements_id INT REFERENCES dim_measurements(measurements_id),
    diagnosis_type_id INT REFERENCES dim_diagnosis_type(diagnosis_type_id),
    date_id INT REFERENCES dim_date(date_id)
);

-- =============================================
-- INDEX pour optimisation des performances
-- =============================================

-- Index sur les cles etrangeres de fact_breast_clinical
CREATE INDEX idx_fact_bc_patient ON fact_breast_clinical(patient_id);
CREATE INDEX idx_fact_bc_diagnosis ON fact_breast_clinical(diagnosis_id);
CREATE INDEX idx_fact_bc_outcome ON fact_breast_clinical(outcome_id);
CREATE INDEX idx_fact_bc_date ON fact_breast_clinical(date_id);

-- Index sur fact_lung_survey
CREATE INDEX idx_fact_ls_symptoms ON fact_lung_survey(symptoms_id);
CREATE INDEX idx_fact_ls_risk ON fact_lung_survey(risk_factors_id);
CREATE INDEX idx_fact_ls_date ON fact_lung_survey(date_id);
CREATE INDEX idx_fact_ls_cancer ON fact_lung_survey(lung_cancer);
CREATE INDEX idx_fact_ls_gender ON fact_lung_survey(gender);

-- Index sur fact_breast_diagnostic
CREATE INDEX idx_fact_bd_measurements ON fact_breast_diagnostic(measurements_id);
CREATE INDEX idx_fact_bd_diagnosis ON fact_breast_diagnostic(diagnosis_type_id);
CREATE INDEX idx_fact_bd_date ON fact_breast_diagnostic(date_id);

-- =============================================
-- Insertion des donnees de reference
-- =============================================

-- Date par defaut pour les donnees sans timestamp
INSERT INTO dim_date (full_date, year, month, quarter)
VALUES ('2020-01-01', 2020, 1, 1);

-- Types de diagnostic pour Breast Diagnostic
INSERT INTO dim_diagnosis_type (diagnosis_code, diagnosis_label)
VALUES 
    ('M', 'Malignant'),
    ('B', 'Benign');

-- =============================================
-- Vues utiles pour l'analyse
-- =============================================

-- Vue: Resume Breast Clinical
CREATE OR REPLACE VIEW v_breast_clinical_summary AS
SELECT 
    fc.id,
    p.age,
    p.race,
    p.marital_status,
    d.t_stage,
    d.n_stage,
    d.stage_6th,
    d.grade,
    o.status,
    fc.tumor_size,
    fc.survival_months
FROM fact_breast_clinical fc
JOIN dim_patient p ON fc.patient_id = p.patient_id
JOIN dim_diagnosis d ON fc.diagnosis_id = d.diagnosis_id
JOIN dim_outcome o ON fc.outcome_id = o.outcome_id;

-- Vue: Resume Lung Survey
CREATE OR REPLACE VIEW v_lung_survey_summary AS
SELECT 
    ls.id,
    ls.gender,
    ls.age,
    s.smoking,
    s.chronic_disease,
    s.alcohol_consuming,
    sy.coughing,
    sy.chest_pain,
    sy.shortness_breath,
    ls.lung_cancer,
    ls.risk_score,
    ls.symptom_severity
FROM fact_lung_survey ls
JOIN dim_risk_factors s ON ls.risk_factors_id = s.risk_factors_id
JOIN dim_symptoms sy ON ls.symptoms_id = sy.symptoms_id;

-- Vue: Resume Breast Diagnostic
CREATE OR REPLACE VIEW v_breast_diagnostic_summary AS
SELECT 
    bd.id,
    bd.patient_id,
    dt.diagnosis_label,
    m.radius_mean,
    m.texture_mean,
    m.area_mean,
    m.perimeter_mean,
    m.concavity_mean,
    m.worst_avg
FROM fact_breast_diagnostic bd
JOIN dim_diagnosis_type dt ON bd.diagnosis_type_id = dt.diagnosis_type_id
JOIN dim_measurements m ON bd.measurements_id = m.measurements_id;

COMMENT ON SCHEMA public IS 'Data Warehouse multi-sources pour analyse du cancer';
