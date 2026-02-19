import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load datasets
df_health = pd.read_csv('data/Sleep_health_and_lifestyle_dataset.csv')
df_efficiency = pd.read_csv('data/Sleep_Efficiency.csv')

# 1. Standardize Target Variable
# df_health 'Quality of Sleep' is 1-10 -> map to 0-100
df_health['sleep_score'] = df_health['Quality of Sleep'] * 10

# df_efficiency 'Sleep efficiency' is 0-1 -> map to 0-100
df_efficiency['sleep_score'] = df_efficiency['Sleep efficiency'] * 100

# 2. Standardize Features
# Target columns for the final model
# ['age', 'gender', 'sleep_duration_hr', 'heart_rate', 'stress_level', 'rem_percent', 'deep_percent', 'awakenings']

# Process Health Dataset
df_health_sub = df_health[['Age', 'Gender', 'Sleep Duration', 'Heart Rate', 'Stress Level']].copy()
df_health_sub.columns = ['age', 'gender', 'sleep_duration_hr', 'heart_rate', 'stress_level']
df_health_sub['sleep_score'] = df_health['sleep_score']
# Add missing columns with NaN
df_health_sub['rem_percent'] = np.nan
df_health_sub['deep_percent'] = np.nan
df_health_sub['awakenings'] = np.nan

# Process Efficiency Dataset
df_efficiency_sub = df_efficiency[['Age', 'Gender', 'Sleep duration']].copy()
df_efficiency_sub.columns = ['age', 'gender', 'sleep_duration_hr']
df_efficiency_sub['sleep_score'] = df_efficiency['sleep_score']
df_efficiency_sub['rem_percent'] = df_efficiency['REM sleep percentage']
df_efficiency_sub['deep_percent'] = df_efficiency['Deep sleep percentage']
df_efficiency_sub['awakenings'] = df_efficiency['Awakenings']
# Add missing columns with NaN
df_efficiency_sub['heart_rate'] = np.nan
df_efficiency_sub['stress_level'] = np.nan

# 3. Merge
df_merged = pd.concat([df_health_sub, df_efficiency_sub], axis=0, ignore_index=True)

# 4. Save merged data
df_merged.to_csv('data/processed_training_data.csv', index=False)
print(f"Merged dataset created with {len(df_merged)} rows.")
print(df_merged.head())
print(df_merged.describe())
