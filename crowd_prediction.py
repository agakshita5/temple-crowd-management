# # crowd_prediction.py
# import pandas as pd
# from datetime import datetime
# import sqlite3
# import random

# def predict_crowd(date, temple_name):
#     # Connect to database to get historical data
#     conn = sqlite3.connect('pilgrim.db')
    
#     # For this demo, we'll use a simple prediction algorithm
#     # In a real application, you would use a trained ML model
    
#     # Factors affecting crowd:
#     day_of_week = date.weekday()  # 0=Monday, 6=Sunday
#     is_weekend = 1 if day_of_week >= 5 else 0
#     month = date.month
    
#     # Check if it's a holiday (simplified)
#     holidays = [
#         (1, 1),   # New Year
#         (1, 14),  # Makar Sankranti
#         (3, 8),   # Holi (approx)
#         (8, 15),  # Independence Day
#         (10, 2),  # Gandhi Jayanti
#         (12, 25)  # Christmas
#     ]
    
#     is_holiday = 1 if (month, date.day) in holidays else 0
    
#     # Base crowd for the temple
#     base_crowd = {
#         "Somnath": 15000,
#         "Dwarka": 12000,
#         "Ambaji": 10000,
#         "Pavagadh": 8000
#     }.get(temple_name, 10000)
    
#     # Adjust based on factors
#     weekend_factor = 1.5 if is_weekend else 1
#     holiday_factor = 2.0 if is_holiday else 1
#     month_factor = 1.2 if month in [10, 11, 12] else 1  # Festival season
    
#     predicted_crowd = base_crowd * weekend_factor * holiday_factor * month_factor
    
#     # Add some random variation
#     variation = random.uniform(0.9, 1.1)
#     predicted_crowd = int(predicted_crowd * variation)
    
#     conn.close()
#     return predicted_crowd

# def initialize_historical_data():
#     # This function would load the provided CSV into the database
#     # For this demo, we'll just create some sample data
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
    
#     # Create table if not exists
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS historical_data (
#             id INTEGER PRIMARY KEY,
#             date TEXT,
#             temple_name TEXT,
#             estimated_footfall INTEGER
#         )
#     ''')
    
#     # Check if data already exists
#     cursor.execute('SELECT COUNT(*) FROM historical_data')
#     count = cursor.fetchone()[0]
    
#     if count == 0:
#         # Insert sample data
#         temples = ["Somnath", "Dwarka", "Ambaji", "Pavagadh"]
#         for i in range(60):
#             date = (datetime.now() - timedelta(days=i)).date()
#             temple = random.choice(temples)
#             footfall = predict_crowd(date, temple)
            
#             cursor.execute('''
#                 INSERT INTO historical_data (date, temple_name, estimated_footfall)
#                 VALUES (?, ?, ?)
#             ''', (date.isoformat(), temple, footfall))
    
#     conn.commit()
#     conn.close()


# import sqlite3
# from datetime import datetime
# import random
# import pandas as pd

# def predict_crowd(date, temple_name):
#     """
#     Predict crowd based on historical data and external factors
#     """
#     # Connect to database
#     conn = sqlite3.connect('pilgrim.db')
    
#     # Get day of week and month
#     day_of_week = date.weekday()  # 0=Monday, 6=Sunday
#     is_weekend = 1 if day_of_week >= 5 else 0
#     month = date.month
    
#     # Check if it's a holiday (simplified list)
#     holidays = [
#         (1, 1),   # New Year
#         (1, 14),  # Makar Sankranti
#         (3, 8),   # Holi (approx)
#         (8, 15),  # Independence Day
#         (10, 2),  # Gandhi Jayanti
#         (12, 25)  # Christmas
#     ]
    
#     is_holiday = 1 if (month, date.day) in holidays else 0
    
#     # Base crowd for the temple
#     base_crowd = {
#         "Somnath": 15000,
#         "Dwarka": 12000,
#         "Ambaji": 10000,
#         "Pavagadh": 8000
#     }.get(temple_name, 10000)
    
#     # Adjust based on factors
#     weekend_factor = 1.5 if is_weekend else 1
#     holiday_factor = 2.0 if is_holiday else 1
#     month_factor = 1.2 if month in [10, 11, 12] else 1  # Festival season
    
#     predicted_crowd = base_crowd * weekend_factor * holiday_factor * month_factor
    
#     # Add some random variation
#     variation = random.uniform(0.9, 1.1)
#     predicted_crowd = int(predicted_crowd * variation)
    
#     # Save prediction to historical data
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT OR REPLACE INTO historical_data (date, temple_name, estimated_footfall)
#         VALUES (?, ?, ?)
#     ''', (date.date().isoformat(), temple_name, predicted_crowd))
    
#     conn.commit()
#     conn.close()
    
#     return predicted_crowd

# def get_crowd_level(prediction):
#     """
#     Return crowd level based on prediction
#     """
#     if prediction < 10000:
#         return "Low"
#     elif prediction < 30000:
#         return "Moderate"
#     else:
#         return "High"

# def get_recommendation(prediction):
#     """
#     Get recommendation based on crowd prediction
#     """
#     if prediction < 10000:
#         return "Good time to visit"
#     elif prediction < 30000:
#         return "Moderate crowding expected"
#     else:
#         return "High crowding expected - consider another day"



import sqlite3
from datetime import datetime
import random

def predict_crowd(date, temple_name):
    conn = sqlite3.connect('pilgrim.db')
    
    day_of_week = date.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    month = date.month

    holidays = [(1,1),(1,14),(3,8),(8,15),(10,2),(12,25)]
    is_holiday = 1 if (month, date.day) in holidays else 0

    base_crowd = {"Somnath":15000,"Dwarka":12000,"Ambaji":10000,"Pavagadh":8000}.get(temple_name,10000)

    weekend_factor = 1.5 if is_weekend else 1
    holiday_factor = 2.0 if is_holiday else 1
    month_factor = 1.2 if month in [10,11,12] else 1

    predicted_crowd = int(base_crowd * weekend_factor * holiday_factor * month_factor * random.uniform(0.9,1.1))

    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO historical_data (date, temple_name, estimated_footfall)
        VALUES (?, ?, ?)
    ''', (date.date().isoformat(), temple_name, predicted_crowd))
    
    conn.commit()
    conn.close()
    return predicted_crowd

def get_crowd_level(prediction):
    if prediction < 10000: return "Low"
    elif prediction < 30000: return "Moderate"
    else: return "High"

def get_recommendation(prediction):
    if prediction < 10000: return "Good time to visit"
    elif prediction < 30000: return "Moderate crowding expected"
    else: return "High crowding expected - consider another day"
