import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

# Load processed data
df = pd.read_csv('data/processed_training_data.csv')

# Define features and target
X = df.drop('sleep_score', axis=1)
y = df['sleep_score']

# Separate features by type
numeric_features = ['age', 'sleep_duration_hr', 'heart_rate', 'stress_level', 'rem_percent', 'deep_percent', 'awakenings']
categorical_features = ['gender']

# Preprocessing Pipeline
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# Training Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Full Pipeline with Model
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# Fit Model
print("Training RandomForestRegressor...")
model_pipeline.fit(X_train, y_train)

# Evaluate
y_pred = model_pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Model Results: MAE={mae:.2f}, R2={r2:.2f}")

# Save artifacts
if not os.path.exists('models'):
    os.makedirs('models')

joblib.dump(model_pipeline, 'models/sleep_model_pipeline.pkl')
print("Model pipeline saved to models/sleep_model_pipeline.pkl")
