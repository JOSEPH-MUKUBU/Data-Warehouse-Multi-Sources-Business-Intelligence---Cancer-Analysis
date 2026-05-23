"""
Module de transformations de donnees pour le Data Warehouse multi-sources
Fournit des utilitaires pour la normalisation, l'encodage et les calculs derives
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class DataTransformer:
    """Classe pour les transformations de donnees standardisees"""
    
    @staticmethod
    def normalize_minmax(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Normalisation Min-Max: ramene les valeurs dans [0, 1]
        
        Args:
            df: DataFrame source
            columns: Liste des colonnes a normaliser
            
        Returns:
            DataFrame avec colonnes normalisees
        """
        df_normalized = df.copy()
        for col in columns:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                if max_val > min_val:
                    df_normalized[col] = (df[col] - min_val) / (max_val - min_val)
                else:
                    df_normalized[col] = 0
        return df_normalized
    
    @staticmethod
    def normalize_standard(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Normalisation Standard (Z-score): moyenne=0, ecart-type=1
        
        Args:
            df: DataFrame source
            columns: Liste des colonnes a normaliser
            
        Returns:
            DataFrame avec colonnes normalisees
        """
        df_normalized = df.copy()
        for col in columns:
            if col in df.columns:
                mean_val = df[col].mean()
                std_val = df[col].std()
                if std_val > 0:
                    df_normalized[col] = (df[col] - mean_val) / std_val
                else:
                    df_normalized[col] = 0
        return df_normalized
    
    @staticmethod
    def bin_age_groups(ages: pd.Series, bins: List[int], labels: List[str]) -> pd.Series:
        """
        Regroupement des ages en categories
        
        Args:
            ages: Serie des ages
            bins: Limites des bins [0, 30, 40, 50, ...]
            labels: Labels pour chaque groupe
            
        Returns:
            Serie avec categories d'age
        """
        return pd.cut(ages, bins=bins, labels=labels, right=False)
    
    @staticmethod
    def encode_binary_features(df: pd.DataFrame, columns: List[str], 
                               mapping: Dict[int, int]) -> pd.DataFrame:
        """
        Encode les features binaires selon un mapping donne
        
        Args:
            df: DataFrame source
            columns: Colonnes a encoder
            mapping: Dictionnaire de mapping (ex: {1: 0, 2: 1})
            
        Returns:
            DataFrame avec colonnes encodees
        """
        df_encoded = df.copy()
        for col in columns:
            if col in df.columns:
                df_encoded[col] = df[col].map(mapping)
        return df_encoded
    
    @staticmethod
    def encode_yes_no(series: pd.Series) -> pd.Series:
        """
        Convertit YES/NO en 1/0
        
        Args:
            series: Serie avec valeurs YES/NO
            
        Returns:
            Serie avec 1/0
        """
        mapping = {'YES': 1, 'Yes': 1, 'yes': 1, 'NO': 0, 'No': 0, 'no': 0}
        return series.map(mapping)
    
    @staticmethod
    def encode_gender(series: pd.Series) -> pd.Series:
        """
        Encode gender M/F en 1/0
        
        Args:
            series: Serie avec M/F
            
        Returns:
            Serie avec 1/0 (M=1, F=0)
        """
        mapping = {'M': 1, 'Male': 1, 'F': 0, 'Female': 0}
        return series.map(mapping)
    
    @staticmethod
    def calculate_risk_score(df: pd.DataFrame, 
                            smoking_col: str = 'smoking',
                            chronic_col: str = 'chronic_disease',
                            alcohol_col: str = 'alcohol_consuming',
                            age_col: str = 'age',
                            weights: Optional[Dict[str, float]] = None) -> pd.Series:
        """
        Calcule un score de risque composite base sur plusieurs facteurs
        
        Args:
            df: DataFrame source
            smoking_col: Nom colonne smoking
            chronic_col: Nom colonne chronic disease
            alcohol_col: Nom colonne alcohol
            age_col: Nom colonne age
            weights: Poids pour chaque facteur
            
        Returns:
            Serie avec scores de risque [0, 1]
        """
        if weights is None:
            weights = {
                'smoking': 0.30,
                'chronic': 0.20,
                'alcohol': 0.15,
                'age': 0.35
            }
        
        # Normaliser l'age
        age_normalized = (df[age_col] - df[age_col].min()) / (df[age_col].max() - df[age_col].min())
        
        # Calculer le score
        risk_score = (
            df[smoking_col] * weights['smoking'] +
            df[chronic_col] * weights['chronic'] +
            df[alcohol_col] * weights['alcohol'] +
            age_normalized * weights['age']
        )
        
        return risk_score
    
    @staticmethod
    def calculate_symptom_severity(df: pd.DataFrame, symptom_cols: List[str]) -> pd.Series:
        """
        Calcule un score de severite des symptomes
        
        Args:
            df: DataFrame source
            symptom_cols: Liste des colonnes de symptomes
            
        Returns:
            Serie avec score de severite [0, 1]
        """
        return df[symptom_cols].mean(axis=1)
    
    @staticmethod
    def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> pd.Series:
        """
        Detecte les valeurs aberrantes avec la methode IQR
        
        Args:
            series: Serie de donnees
            multiplier: Multiplicateur IQR (defaut 1.5)
            
        Returns:
            Serie booleenne (True = outlier)
        """
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        return (series < lower_bound) | (series > upper_bound)
    
    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Nettoie les noms de colonnes (espaces, majuscules, etc.)
        
        Args:
            df: DataFrame source
            
        Returns:
            DataFrame avec noms de colonnes nettoyes
        """
        df_clean = df.copy()
        df_clean.columns = df_clean.columns.str.strip().str.lower().str.replace(' ', '_')
        return df_clean
    
    @staticmethod
    def create_composite_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Cree des features composites pour breast diagnostic
        
        Args:
            df: DataFrame avec mesures
            
        Returns:
            DataFrame avec nouvelles features
        """
        df_enhanced = df.copy()
        
        # Ratios utiles
        if 'radius_mean' in df.columns and 'texture_mean' in df.columns:
            df_enhanced['radius_texture_ratio'] = df['radius_mean'] / (df['texture_mean'] + 1e-6)
        
        if 'area_mean' in df.columns and 'perimeter_mean' in df.columns:
            df_enhanced['area_perimeter_ratio'] = df['area_mean'] / (df['perimeter_mean'] + 1e-6)
        
        # Moyenne des pires mesures
        worst_cols = [col for col in df.columns if 'worst' in col]
        if worst_cols:
            df_enhanced['worst_avg'] = df[worst_cols].mean(axis=1)
        
        return df_enhanced


class DataValidator:
    """Classe pour la validation des donnees"""
    
    @staticmethod
    def validate_range(series: pd.Series, min_val: float, max_val: float) -> Tuple[bool, List]:
        """
        Valide que les valeurs sont dans une plage donnee
        
        Returns:
            (is_valid, list_of_invalid_indices)
        """
        invalid = series[(series < min_val) | (series > max_val)].index.tolist()
        return len(invalid) == 0, invalid
    
    @staticmethod
    def validate_not_null(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, Dict]:
        """
        Valide l'absence de valeurs NULL
        
        Returns:
            (is_valid, dict_of_null_counts)
        """
        null_counts = {}
        for col in columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    null_counts[col] = null_count
        
        return len(null_counts) == 0, null_counts
    
    @staticmethod
    def check_data_quality(df: pd.DataFrame) -> Dict:
        """
        Rapport de qualite des donnees
        
        Returns:
            Dictionnaire avec metriques de qualite
        """
        return {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024**2  # MB
        }
