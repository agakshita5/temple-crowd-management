import numpy as np
import pandas as pd

date_range = pd.date_range(start='2024-01-01', end='2025-08-31', freq='D')
darshan_slots = ['6-7', '7-8', '8-9', '9-10', '10-11', '11-12',
                 '12-1', '1-2', '2-3', '3-4', '4-5', '5-6']

slot_probs = [0.15, 0.15, 0.15, 0.10, 0.10, 0.10, 0.075, 0.075, 0.025, 0.025, 0.015, 0.015]
slot_probs = np.array(slot_probs)
slot_probs /= slot_probs.sum()

festival_months = [1, 3, 8, 10]
rows = []

for _ in range(50000):
    d = np.random.choice(date_range)
    d = pd.Timestamp(d)
    month = d.month
    day_of_week = d.strftime('%A')
    
    # Festival flag: Higher chance in festival months
    festival_flag = int(month in festival_months and np.random.rand() < 0.4)
    
    # Holiday flag: weekend or random special
    holiday_flag = int(day_of_week in ['Saturday', 'Sunday'] or np.random.rand() < 0.06)
    
    # Season encoding
    if month == 12 or month <= 2:
        season = 1  # Winter
    elif 3 <= month <= 5:
        season = 2  # Summer
    elif 6 <= month <= 8:
        season = 3  # Monsoon
    else:
        season = 4  # Autumn
    
    # Special event flag: Rare
    special_event_flag = int(np.random.rand() < 0.07)
    
    # Darshan slot choice
    slot = np.random.choice(darshan_slots, p=slot_probs)

    # Calculate crowd level
    crowd_prob = 0.3  
    
    if festival_flag == 1:
        crowd_prob += 0.3
    if holiday_flag == 1:
        crowd_prob += 0.2
    if slot in ['6-7', '7-8', '8-9']:  # Morning slots
        crowd_prob += 0.2
    if season == 1:  # Winter
        crowd_prob += 0.1
    if special_event_flag == 1:
        crowd_prob += 0.4
    
    # some randomness
    crowd_prob += np.random.uniform(-0.1, 0.1)
    
    crowd_prob = max(0.05, min(0.95, crowd_prob))

    if crowd_prob < 0.4:
        crowd_level = 0  # Low
    elif crowd_prob < 0.7:
        crowd_level = 1  # Medium
    else:
        crowd_level = 2  # High

    rows.append({
        'date': d.strftime('%Y-%m-%d'),
        'day_of_week': day_of_week,
        'month': month,
        'festival_flag': festival_flag,
        'darshan_slot': slot,
        'holiday_flag': holiday_flag,
        'season': season,
        'special_event_flag': special_event_flag,
        'crowd_level': crowd_level
    })


df = pd.DataFrame(rows)
print(f"Unique crowd levels: {df['crowd_level'].unique()}")
print(f"Count of each crowd level:\n{df['crowd_level'].value_counts()}")

df.to_csv('admin/synthetic_gujarat_temple_crowd.csv', index=False)