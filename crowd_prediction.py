import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import joblib

df = pd.read_csv('data/synthetic_gujarat_temple_crowd.csv')

# Prepare features and target
X = df[['day_of_week', 'month', 'festival_flag', 'darshan_slot', 'holiday_flag', 'season', 'special_event_flag']]
y = df['crowd_level']

# Encode categorical variables
le_day = LabelEncoder()
le_slot = LabelEncoder()


X_encoded = X.copy() # fix the SettingWithCopyWarning by using .copy()
X_encoded['day_of_week'] = le_day.fit_transform(X['day_of_week'])
X_encoded['darshan_slot'] = le_slot.fit_transform(X['darshan_slot'])

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42, stratify=y)

model = XGBClassifier(
    n_estimators=100, 
    random_state=42, 
    objective='multi:softprob',
    num_class=3, 
    eval_metric='mlogloss'
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")

joblib.dump(model, 'crowd_prediction_model.pkl')
joblib.dump(le_day, 'day_encoder.pkl')
joblib.dump(le_slot, 'slot_encoder.pkl')
print("Model and encoders saved successfully!")