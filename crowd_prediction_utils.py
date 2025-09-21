# # crowd_prediction_utils.py
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import joblib
# from sklearn.preprocessing import LabelEncoder

# # Load model and encoders (you'll need to train this first)
# try:
#     ml_model = joblib.load('crowd_prediction_model.pkl')
#     le_day = joblib.load('day_encoder.pkl')
#     le_slot = joblib.load('slot_encoder.pkl')
#     ml_model_available = True
# except:
#     ml_model_available = False

# # Festival calendar (you can expand this)
# FESTIVAL_DATES = {
#     '2024-01-14': 'Makar Sankranti',
#     '2024-01-26': 'Republic Day',
#     '2024-03-08': 'Maha Shivaratri',
#     '2024-03-25': 'Holi',
#     '2024-04-09': 'Ugadi',
#     '2024-04-17': 'Ram Navami',
#     '2024-05-23': 'Buddha Purnima',
#     '2024-08-26': 'Janmashtami',
#     '2024-09-07': 'Ganesh Chaturthi',
#     '2024-10-02': 'Gandhi Jayanti',
#     '2024-10-12': 'Dussehra',
#     '2024-11-01': 'Diwali',
#     '2024-12-25': 'Christmas',
#     '2025-01-14': 'Makar Sankranti',
#     '2025-01-26': 'Republic Day',
#     '2025-02-26': 'Maha Shivaratri',
#     '2025-03-25': 'Holi',
#     '2025-04-09': 'Ugadi',
#     '2025-04-17': 'Ram Navami',
#     '2025-05-23': 'Buddha Purnima',
#     '2025-08-16': 'Janmashtami',
#     '2025-09-27': 'Ganesh Chaturthi',
#     '2025-10-02': 'Gandhi Jayanti',
#     '2025-09-22': 'Navratri',
#     '2025-09-30': 'Asthmi',
#     '2025-10-01': 'Mahanavami',
#     '2025-10-02': 'Dussehra',
#     '2025-10-20': 'Diwali',
#     '2025-12-25': 'Christmas',
# }

# def is_festival_date(date_str):
#     """Check if a date is a festival date"""
#     return date_str in FESTIVAL_DATES

# # def predict_crowd_level_ml(date_str, darshan_slot):
# #     # If model is not available, return random prediction
# #     if ml_model is None:
# #         return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])
    
# #     try:
# #         # Convert date string to datetime
# #         date = datetime.strptime(date_str, '%Y-%m-%d')
        
# #         # Extract features from date
# #         day_of_week = date.strftime('%A')  # Full day name
# #         month = date.month
        
# #         # Determine season
# #         if month in [11, 12, 1, 2]:
# #             season = 1  # Winter
# #         elif month in [3, 4, 5]:
# #             season = 2  # Summer
# #         elif month in [6, 7, 8, 9]:
# #             season = 3  # Monsoon
# #         else:
# #             season = 4  # Autumn
        
# #         # Festival flag (you might want to create a festival calendar)
# #         festival_months = [1, 3, 8, 10]  # Example festival months
# #         festival_flag = 1 if month in festival_months else 0
        
# #         # Holiday flag (weekend)
# #         holiday_flag = 1 if date.weekday() >= 5 else 0
        
# #         # Special event flag (you might want to create an event calendar)
# #         special_event_flag = 0  # Default to 0
        
# #         # Encode categorical features
# #         try:
# #             encoded_day = le_day.transform([day_of_week])[0]
# #         except:
# #             encoded_day = le_day.transform(['Monday'])[0]  # Default to Monday
        
# #         try:
# #             encoded_slot = le_slot.transform([darshan_slot])[0]
# #         except:
# #             encoded_slot = le_slot.transform(['6-7'])[0]  # Default to 6-7 slot
        
# #         # Create feature array
# #         features = np.array([[encoded_day, month, festival_flag, encoded_slot, 
# #                             holiday_flag, season, special_event_flag]])
        
# #         # Make prediction
# #         prediction = ml_model.predict(features)[0]
        
# #         # Map prediction to crowd level
# #         crowd_levels = {0: 'Low', 1: 'Medium', 2: 'High'}
# #         return crowd_levels.get(prediction, 'Medium')
    
# #     except Exception as e:
# #         print(f"Error in ML prediction: {e}")
# #         # Fallback to random prediction
# #         return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])

# def predict_crowd_ml(date_str, darshan_slot):
#     """
#     ML-based prediction for crowd level
#     """
#     if not ml_model_available:
#         return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])
    
#     try:
#         date = datetime.strptime(date_str, '%Y-%m-%d')
#         day_of_week = date.strftime('%A')
#         month = date.month
        
#         # Determine season
#         if month in [11, 12, 1, 2]:
#             season = 1  # Winter
#         elif month in [3, 4, 5]:
#             season = 2  # Summer
#         elif month in [6, 7, 8, 9]:
#             season = 3  # Monsoon
#         else:
#             season = 4  # Autumn
        
#         # Festival flag
#         festival_months = [1, 3, 8, 10]
#         festival_flag = 1 if month in festival_months else 0
        
#         # Holiday flag (weekend)
#         holiday_flag = 1 if date.weekday() >= 5 else 0
        
#         # Special event flag
#         special_event_flag = 0
        
#         # Encode categorical features
#         try:
#             encoded_day = le_day.transform([day_of_week])[0]
#         except:
#             encoded_day = le_day.transform(['Monday'])[0]
        
#         try:
#             encoded_slot = le_slot.transform([darshan_slot])[0]
#         except:
#             encoded_slot = le_slot.transform(['6-7'])[0]
        
#         # Create feature array and predict
#         features = np.array([[encoded_day, month, festival_flag, encoded_slot, 
#                             holiday_flag, season, special_event_flag]])
#         prediction = ml_model.predict(features)[0]
        
#         crowd_levels = {0: 'Low', 1: 'Medium', 2: 'High'}
#         return crowd_levels.get(prediction, 'Medium')
    
#     except Exception as e:
#         print(f"Error in ML prediction: {e}")
#         return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])

# def predict_crowd_heuristic(date, temple_name):
#     """
#     Heuristic-based prediction for crowd size
#     """
#     day_of_week = date.weekday()
#     is_weekend = 1 if day_of_week >= 5 else 0
#     month = date.month
    
#     holidays = [
#         (1, 1), (1, 14), (3, 8), (8, 15), 
#         (10, 2), (12, 25)
#     ]
    
#     is_holiday = 1 if (month, date.day) in holidays else 0
    
#     base_crowd = {
#         "Somnath": 15000,
#         "Dwarka": 12000,
#         "Ambaji": 10000,
#         "Pavagadh": 8000
#     }.get(temple_name, 10000)
    
#     weekend_factor = 1.5 if is_weekend else 1
#     holiday_factor = 2.0 if is_holiday else 1
#     month_factor = 1.2 if month in [10, 11, 12] else 1
    
#     predicted_crowd = base_crowd * weekend_factor * holiday_factor * month_factor
#     predicted_crowd = int(predicted_crowd * random.uniform(0.9, 1.1))
    
#     # Save to database
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT OR REPLACE INTO historical_data (date, temple_name, estimated_footfall)
#         VALUES (?, ?, ?)
#     ''', (date.date().isoformat(), temple_name, predicted_crowd))
#     conn.commit()
#     conn.close()
    
#     return predicted_crowd

# def get_crowd_level(prediction):
#     """Convert numerical prediction to level"""
#     if prediction < 10000:
#         return "Low"
#     elif prediction < 30000:
#         return "Moderate"
#     else:
#         return "High"

# def get_recommendation(prediction):
#     """Get recommendation based on prediction"""
#     if prediction < 10000:
#         return "Good time to visit"
#     elif prediction < 30000:
#         return "Moderate crowding expected"
#     else:
#         return "High crowding expected - consider another day"

# def unified_predict(date_str, temple_name, darshan_slot=None):

#     """
#     Unified prediction function for your app
    
#     Parameters:
#     date_str: string in format 'YYYY-MM-DD'
#     temple_name: string name of temple
#     darshan_slot: optional string like '6-7', '7-8', etc.
    
#     Returns:
#     Dictionary with crowd prediction and recommendations
#     """
#     date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
#     # Use ML prediction if slot is provided
#     if darshan_slot:
#         crowd_level = predict_crowd_ml(date_str, darshan_slot)
        
#         # Convert level to numerical estimate for consistency
#         level_map = {"Low": 5000, "Medium": 15000, "High": 35000}
#         numerical_estimate = level_map.get(crowd_level, 15000)
        
#         return {
#             "crowd_level": crowd_level,
#             "estimated_footfall": numerical_estimate,
#             "recommendation": get_recommendation(numerical_estimate)
#         }
#     else:
#         # Use heuristic prediction
#         numerical_estimate = predict_crowd_heuristic(date_obj, temple_name)
#         crowd_level = get_crowd_level(numerical_estimate)
        
#         return {
#             "crowd_level": crowd_level,
#             "estimated_footfall": numerical_estimate,
#             "recommendation": get_recommendation(numerical_estimate)
#         }

# crowd_prediction_utils.py
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
from sklearn.preprocessing import LabelEncoder
import sqlite3
import random

# Load model and encoders for slot prediction
try:
    model = joblib.load('crowd_prediction_model.pkl')
    le_day = joblib.load('day_encoder.pkl')
    le_slot = joblib.load('slot_encoder.pkl')
    model_available = True
except:
    model_available = False

# Festival calendar
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
    '2024-12-25': 'Christmas',
    '2025-01-14': 'Makar Sankranti',
    '2025-01-26': 'Republic Day',
    '2025-02-26': 'Maha Shivaratri',
    '2025-03-25': 'Holi',
    '2025-04-09': 'Ugadi',
    '2025-04-17': 'Ram Navami',
    '2025-05-23': 'Buddha Purnima',
    '2025-08-16': 'Janmashtami',
    '2025-09-27': 'Ganesh Chaturthi',
    '2025-10-02': 'Gandhi Jayanti',
    '2025-09-22': 'Navratri',
    '2025-09-30': 'Asthmi',
    '2025-10-01': 'Mahanavami',
    '2025-10-02': 'Dussehra',
    '2025-10-20': 'Diwali',
    '2025-12-25': 'Christmas',
}

def is_festival_date(date_str):
    """Check if a date is a festival date"""
    return date_str in FESTIVAL_DATES

def predict_crowd_slot_level(date_str, darshan_slot):
    """
    Predict crowd level for a specific time slot (your original function)
    
    Parameters:
    date_str: string in format 'YYYY-MM-DD'
    darshan_slot: string like '6-7', '7-8', etc.
    
    Returns:
    crowd_level: string ('Low', 'Medium', 'High')
    """
    # If model is not available, return random prediction
    if not model_available:
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
        
        # Festival flag
        festival_months = [1, 3, 8, 10]  # Example festival months
        festival_flag = 1 if month in festival_months else 0
        
        # Holiday flag (weekend)
        holiday_flag = 1 if date.weekday() >= 5 else 0
        
        # Special event flag
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
        print(f"Error in slot prediction: {e}")
        # Fallback to random prediction
        return np.random.choice(['Low', 'Medium', 'High'], p=[0.3, 0.4, 0.3])

def predict_crowd_temple_level(date_str, temple_name):
    """
    Predict crowd level for a temple (daily prediction without specific slot)
    
    Parameters:
    date_str: string in format 'YYYY-MM-DD'
    temple_name: string name of temple
    
    Returns:
    Dictionary with crowd_level, estimated_footfall, and recommendation
    """
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        day_of_week = date.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        month = date.month
        
        # Check if it's a holiday
        holidays = [
            (1, 1),   # New Year
            (1, 14),  # Makar Sankranti
            (3, 8),   # Holi (approx)
            (8, 15),  # Independence Day
            (10, 2),  # Gandhi Jayanti
            (12, 25)  # Christmas
        ]
        
        is_holiday = 1 if (month, date.day) in holidays else 0
        
        # Base crowd for the temple
        base_crowd = {
            "Somnath": 15000,
            "Dwarka": 12000,
            "Ambaji": 10000,
            "Pavagadh": 8000
        }.get(temple_name, 10000)
        
        # Adjust based on factors
        weekend_factor = 1.5 if is_weekend else 1
        holiday_factor = 2.0 if is_holiday else 1
        month_factor = 1.2 if month in [10, 11, 12] else 1  # Festival season
        
        predicted_crowd = base_crowd * weekend_factor * holiday_factor * month_factor
        
        # Add some random variation
        variation = random.uniform(0.9, 1.1)
        predicted_crowd = int(predicted_crowd * variation)
        
        # Determine crowd level
        if predicted_crowd < 10000:
            crowd_level = "Low"
        elif predicted_crowd < 30000:
            crowd_level = "Moderate"
        else:
            crowd_level = "High"
            
        # Get recommendation
        if predicted_crowd < 10000:
            recommendation = "Good time to visit"
        elif predicted_crowd < 30000:
            recommendation = "Moderate crowding expected"
        else:
            recommendation = "High crowding expected - consider another day"
        
        # Save to database
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO historical_data (date, temple_name, estimated_footfall)
            VALUES (?, ?, ?)
        ''', (date_str, temple_name, predicted_crowd))
        conn.commit()
        conn.close()
        
        return {
            "crowd_level": crowd_level,
            "estimated_footfall": predicted_crowd,
            "recommendation": recommendation
        }
    
    except Exception as e:
        print(f"Error in temple prediction: {e}")
        # Fallback response
        return {
            "crowd_level": "Moderate",
            "estimated_footfall": 15000,
            "recommendation": "Moderate crowding expected"
        }