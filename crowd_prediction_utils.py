# crowd_prediction_utils.py
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
from sklearn.preprocessing import LabelEncoder

# Load model and encoders (you'll need to train this first)
try:
    model = joblib.load('crowd_prediction_model.pkl')
    le_day = joblib.load('day_encoder.pkl')
    le_slot = joblib.load('slot_encoder.pkl')
except:
    # Fallback to random predictions if model not available
    model = None

def predict_crowd_level(date_str, darshan_slot):
    """
    Predict crowd level for a given date and slot
    
    Parameters:
    date_str: string in format 'YYYY-MM-DD'
    darshan_slot: string like '6-7', '7-8', etc.
    
    Returns:
    crowd_level: string ('Low', 'Medium', 'High')
    """
    # If model is not available, return random prediction
    if model is None:
        return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])
    
    try:
        # Convert date string to datetime
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Extract features from date
        day_of_week = date.strftime('%A')  # Full day name
        month = date.month
        
        # Determine season
        if month in [11, 12, 1, 2]:
            season = 1  # Winter
        elif month in [3, 4, 5]:
            season = 2  # Summer
        elif month in [6, 7, 8, 9]:
            season = 3  # Monsoon
        else:
            season = 4  # Autumn
        
        # Festival flag (you might want to create a festival calendar)
        festival_months = [1, 3, 8, 10]  # Example festival months
        festival_flag = 1 if month in festival_months else 0
        
        # Holiday flag (weekend)
        holiday_flag = 1 if date.weekday() >= 5 else 0
        
        # Special event flag (you might want to create an event calendar)
        special_event_flag = 0  # Default to 0
        
        # Encode categorical features
        try:
            encoded_day = le_day.transform([day_of_week])[0]
        except:
            encoded_day = le_day.transform(['Monday'])[0]  # Default to Monday
        
        try:
            encoded_slot = le_slot.transform([darshan_slot])[0]
        except:
            encoded_slot = le_slot.transform(['6-7'])[0]  # Default to 6-7 slot
        
        # Create feature array
        features = np.array([[encoded_day, month, festival_flag, encoded_slot, 
                            holiday_flag, season, special_event_flag]])
        
        # Make prediction
        prediction = model.predict(features)[0]
        
        # Map prediction to crowd level
        crowd_levels = {0: 'Low', 1: 'Medium', 2: 'High'}
        return crowd_levels.get(prediction, 'Medium')
    
    except Exception as e:
        print(f"Error in prediction: {e}")
        # Fallback to random prediction
        return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])

# Festival calendar (you can expand this)
FESTIVAL_DATES = {
    '2024-01-14': 'Makar Sankranti',
    '2024-01-26': 'Republic Day',
    '2024-03-08': 'Maha Shivaratri',
    '2024-03-25': 'Holi',
    '2024-04-09': 'Ugadi',
    '2024-04-17': 'Ram Navami',
    '2024-05-23': 'Buddha Purnima',
    '2024-08-26': 'Janmashtami',
    '2024-09-07': 'Ganesh Chaturthi',
    '2024-10-02': 'Gandhi Jayanti',
    '2024-10-12': 'Dussehra',
    '2024-11-01': 'Diwali',
    '2024-12-25': 'Christmas'
}

def is_festival_date(date_str):
    """Check if a date is a festival date"""
    return date_str in FESTIVAL_DATES