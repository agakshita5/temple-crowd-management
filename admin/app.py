# # app.py (Flask backend)
# from flask import Flask, render_template, request, jsonify, session, redirect, url_for
# import sqlite3
# from datetime import datetime, timedelta
# import json
# import os
# import joblib
# import pandas as pd
# import numpy as np

# app = Flask(__name__, template_folder='../templates')
# app.secret_key = 'pilgrim_secret_key'

# # Helper function to get database connection
# def get_db():
#     conn = sqlite3.connect('../pilgrim.db')
#     conn.row_factory = sqlite3.Row
#     return conn

# # Crowd prediction function
# def predict_crowd_level(temple_name, date, slot_time):
#     try:
#         # Load the trained model and encoders
#         model = joblib.load('crowd_prediction_model.pkl')
#         le_day = joblib.load('day_encoder.pkl')
#         le_slot = joblib.load('slot_encoder.pkl')
        
#         # Parse date to get day of week and month
#         date_obj = datetime.strptime(date, '%Y-%m-%d')
#         day_of_week = date_obj.strftime('%A')
#         month = date_obj.month
        
#         # Determine season based on month
#         if month in [12, 1, 2]:
#             season = 1  # Winter
#         elif month in [3, 4, 5]:
#             season = 2  # Spring
#         elif month in [6, 7, 8]:
#             season = 3  # Summer
#         else:
#             season = 4  # Autumn
        
#         # Check if it's a weekend
#         holiday_flag = 1 if date_obj.weekday() >= 5 else 0
        
#         # Check for festivals (simplified logic)
#         festival_flag = 1 if month in [10, 11] else 0  # Diwali season
        
#         # Special events (simplified)
#         special_event_flag = 0
        
#         # Encode categorical variables
#         try:
#             encoded_day = le_day.transform([day_of_week])[0]
#         except:
#             encoded_day = le_day.transform(['Monday'])[0]
        
#         try:
#             encoded_slot = le_slot.transform([slot_time])[0]
#         except:
#             encoded_slot = le_slot.transform(['06:00 - 07:30'])[0]
        
#         # Prepare features
#         features = np.array([[encoded_day, month, festival_flag, encoded_slot, holiday_flag, season, special_event_flag]])
        
#         # Make prediction
#         prediction = model.predict(features)[0]
        
#         crowd_levels = {0: 'Low', 1: 'Medium', 2: 'High'}
#         return crowd_levels[prediction]
        
#     except Exception as e:
#         print(f"Error in crowd prediction: {e}")
#         return 'Medium'  # Default fallback

# # Admin login route (simplified for demo)
# @app.route('/admin/login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
        
#         # Simple authentication (in real app, use proper authentication)
#         if username == 'admin' and password == 'admin123':
#             session['admin_logged_in'] = True
#             session['admin_temple'] = request.form.get('temple', '1')  # Default to first temple
#             return redirect(url_for('admin_dashboard'))
#         else:
#             return render_template('admin_login.html', error='Invalid credentials')
    
#     return render_template('admin_login.html')

# # Admin dashboard
# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if not session.get('admin_logged_in'):
#         return redirect(url_for('admin_login'))
    
#     temple_name = session.get('admin_temple', 'Somnath Temple')
    
#     # Get today's date
#     today = datetime.now().strftime('%Y-%m-%d')
    
#     conn = get_db()
    
#     # Get today's time slots
#     slots = conn.execute('''SELECT * FROM time_slots 
#                           WHERE temple_name = ? AND slot_date = ? 
#                           ORDER BY slot_time''', (temple_name, today)).fetchall()
    
#     # Get today's bookings with visitor information
#     bookings = conn.execute('''SELECT b.*, u.username, ts.slot_time, 
#                                      v.full_name, v.age, v.phone_number, v.email, v.address
#                               FROM bookings b 
#                               JOIN users u ON b.user_id = u.id 
#                               JOIN time_slots ts ON b.slot_id = ts.id 
#                               LEFT JOIN visitors v ON b.id = v.booking_id
#                               WHERE b.temple_name = ? AND ts.slot_date = ? 
#                               ORDER BY b.booking_time DESC''', (temple_name, today)).fetchall()
    
#     # Get recent medical emergencies
#     emergencies = conn.execute('''SELECT * FROM medical_emergencies 
#                                 ORDER BY created_at DESC LIMIT 10''').fetchall()
    
#     # Get recent incidents
#     incidents = conn.execute('''SELECT * FROM incidents 
#                               ORDER BY timestamp DESC LIMIT 10''').fetchall()
    
#     # Get current slot and predict crowd
#     current_time = datetime.now().time()
#     current_slot = None
#     predicted_crowd = 'Medium'
    
#     for slot in slots:
#         start_time, end_time = slot['slot_time'].split(' - ')
#         start_h, start_m = map(int, start_time.split(':'))
#         end_h, end_m = map(int, end_time.split(':'))
        
#         slot_start = datetime.now().replace(hour=start_h, minute=start_m, second=0, microsecond=0)
#         slot_end = datetime.now().replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        
#         if slot_start.time() <= current_time <= slot_end.time():
#             current_slot = slot
#             predicted_crowd = predict_crowd_level(temple_name, today, slot['slot_time'])
#             break
    
#     # Get comprehensive statistics
#     total_bookings_today = len(bookings)
#     total_visitors_today = conn.execute('''SELECT COUNT(*) FROM visitors v 
#                                          JOIN bookings b ON v.booking_id = b.id 
#                                          JOIN time_slots ts ON b.slot_id = ts.id 
#                                          WHERE ts.slot_date = ?''', (today,)).fetchone()[0]
#     total_emergencies = conn.execute('SELECT COUNT(*) FROM medical_emergencies WHERE status = ?', ('pending',)).fetchone()[0]
#     total_incidents = conn.execute('SELECT COUNT(*) FROM incidents WHERE status = ?', ('reported',)).fetchone()[0]
    
#     # Get total bookings and visitors for all time
#     total_bookings_all_time = conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]
#     total_visitors_all_time = conn.execute('SELECT COUNT(*) FROM visitors').fetchone()[0]
    
#     # Get slot utilization statistics
#     total_slots_today = conn.execute('SELECT SUM(total_slots) FROM time_slots WHERE temple_name = ? AND slot_date = ?', 
#                                    (temple_name, today)).fetchone()[0] or 0
#     booked_slots_today = total_slots_today - conn.execute('SELECT SUM(available_slots) FROM time_slots WHERE temple_name = ? AND slot_date = ?', 
#                                                         (temple_name, today)).fetchone()[0] or 0
#     utilization_percentage = (booked_slots_today / total_slots_today * 100) if total_slots_today > 0 else 0
    
#     # Get crowd prediction for next few slots
#     upcoming_slots = conn.execute('''SELECT * FROM time_slots 
#                                    WHERE temple_name = ? AND slot_date = ? 
#                                    AND slot_time > ? 
#                                    ORDER BY slot_time LIMIT 3''', 
#                                    (temple_name, today, current_time.strftime('%H:%M'))).fetchall()
    
#     upcoming_predictions = []
#     for slot in upcoming_slots:
#         crowd_level = predict_crowd_level(temple_name, today, slot['slot_time'])
#         upcoming_predictions.append({
#             'slot': slot['slot_time'],
#             'crowd_level': crowd_level,
#             'available_slots': slot['available_slots']
#         })
    
#     conn.close()
    
#     return render_template('admin_dashboard.html', 
#                          temple_name=temple_name,
#                          slots=slots, 
#                          bookings=bookings,
#                          emergencies=emergencies, 
#                          incidents=incidents,
#                          current_slot=current_slot,
#                          predicted_crowd=predicted_crowd,
#                          upcoming_predictions=upcoming_predictions,
#                          total_bookings_today=total_bookings_today,
#                          total_visitors_today=total_visitors_today,
#                          total_bookings_all_time=total_bookings_all_time,
#                          total_visitors_all_time=total_visitors_all_time,
#                          total_emergencies=total_emergencies,
#                          total_incidents=total_incidents,
#                          total_slots_today=total_slots_today,
#                          booked_slots_today=booked_slots_today,
#                          utilization_percentage=utilization_percentage,
#                          today=today)

# # API to get slot details
# @app.route('/admin/api/slots/<date>')
# def get_slots(date):
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     temple_name = session.get('admin_temple', 'Somnath Temple')
    
#     conn = get_db()
#     slots = conn.execute('''SELECT * FROM time_slots 
#                           WHERE temple_name = ? AND slot_date = ? 
#                           ORDER BY slot_time''', (temple_name, date)).fetchall()
    
#     result = []
#     for slot in slots:
#         slot_dict = dict(slot)
#         # Add crowd prediction
#         slot_dict['predicted_crowd'] = predict_crowd_level(temple_name, date, slot['slot_time'])
#         result.append(slot_dict)
    
#     conn.close()
#     return jsonify(result)

# # API to update slot capacity
# @app.route('/admin/api/slots/update', methods=['POST'])
# def update_slot():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     data = request.json
#     slot_id = data.get('slot_id')
#     capacity = data.get('capacity')
    
#     conn = get_db()
#     conn.execute('UPDATE slots SET capacity = ? WHERE id = ?', (capacity, slot_id))
#     conn.commit()
#     conn.close()
    
#     return jsonify({'success': True})

# # API to get emergency details
# @app.route('/admin/api/emergencies')
# def get_emergencies():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     conn = get_db()
#     emergencies = conn.execute('''SELECT * FROM medical_emergencies 
#                                 ORDER BY created_at DESC''').fetchall()
    
#     result = []
#     for emergency in emergencies:
#         result.append(dict(emergency))
    
#     conn.close()
#     return jsonify(result)

# # API to update emergency status
# @app.route('/admin/api/emergencies/update', methods=['POST'])
# def update_emergency():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     data = request.json
#     emergency_id = data.get('emergency_id')
#     status = data.get('status')
#     admin_notes = data.get('admin_notes', '')
    
#     conn = get_db()
#     if status == 'resolved':
#         conn.execute('UPDATE medical_emergencies SET status = ?, resolved_at = ?, admin_notes = ? WHERE id = ?', 
#                     (status, datetime.now(), admin_notes, emergency_id))
#     else:
#         conn.execute('UPDATE medical_emergencies SET status = ?, admin_notes = ? WHERE id = ?', 
#                     (status, admin_notes, emergency_id))
#     conn.commit()
#     conn.close()
    
#     return jsonify({'success': True})

# # API to get incidents
# @app.route('/admin/api/incidents')
# def get_incidents():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     conn = get_db()
#     incidents = conn.execute('''SELECT * FROM incidents 
#                               ORDER BY timestamp DESC''').fetchall()
    
#     result = []
#     for incident in incidents:
#         result.append(dict(incident))
    
#     conn.close()
#     return jsonify(result)

# # API to update incident status
# @app.route('/admin/api/incidents/update', methods=['POST'])
# def update_incident():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     data = request.json
#     incident_id = data.get('incident_id')
#     status = data.get('status')
#     notes = data.get('notes', '')
    
#     conn = get_db()
#     conn.execute('UPDATE incidents SET status = ? WHERE id = ?', (status, incident_id))
    
#     # Add incident update record
#     conn.execute('''INSERT INTO incident_updates (incident_id, status, notes, updated_by, timestamp)
#                     VALUES (?, ?, ?, ?, ?)''', 
#                  (incident_id, status, notes, 1, datetime.now()))  # Admin user ID = 1
    
#     conn.commit()
#     conn.close()
    
#     return jsonify({'success': True})

# # API to get real-time dashboard data
# @app.route('/admin/api/dashboard-data')
# def get_dashboard_data():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     temple_name = session.get('admin_temple', 'Somnath Temple')
#     today = datetime.now().strftime('%Y-%m-%d')
    
#     conn = get_db()
    
#     # Get current bookings count
#     bookings_count = conn.execute('''SELECT COUNT(*) FROM bookings b 
#                                    JOIN time_slots ts ON b.slot_id = ts.id 
#                                    WHERE b.temple_name = ? AND ts.slot_date = ?''', 
#                                   (temple_name, today)).fetchone()[0]
    
#     # Get pending emergencies
#     emergencies_count = conn.execute('SELECT COUNT(*) FROM medical_emergencies WHERE status = ?', ('pending',)).fetchone()[0]
    
#     # Get reported incidents
#     incidents_count = conn.execute('SELECT COUNT(*) FROM incidents WHERE status = ?', ('reported',)).fetchone()[0]
    
#     # Get current slot info
#     current_time = datetime.now().time()
#     current_slot = conn.execute('''SELECT * FROM time_slots 
#                                   WHERE temple_name = ? AND slot_date = ? 
#                                   AND slot_time LIKE ?''', 
#                                  (temple_name, today, f"{current_time.strftime('%H:%M')}%")).fetchone()
    
#     conn.close()
    
#     return jsonify({
#         'bookings_count': bookings_count,
#         'emergencies_count': emergencies_count,
#         'incidents_count': incidents_count,
#         'current_slot': dict(current_slot) if current_slot else None,
#         'timestamp': datetime.now().isoformat()
#     })

# # API to get crowd prediction
# @app.route('/admin/api/crowd-prediction')
# def get_crowd_prediction():
#     if not session.get('admin_logged_in'):
#         return jsonify({'error': 'Not authorized'}), 401
    
#     temple_name = session.get('admin_temple', 'Somnath Temple')
#     date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
#     conn = get_db()
#     slots = conn.execute('''SELECT * FROM time_slots 
#                           WHERE temple_name = ? AND slot_date = ? 
#                           ORDER BY slot_time''', (temple_name, date)).fetchall()
    
#     predictions = []
#     for slot in slots:
#         crowd_level = predict_crowd_level(temple_name, date, slot['slot_time'])
#         predictions.append({
#             'slot_time': slot['slot_time'],
#             'crowd_level': crowd_level,
#             'available_slots': slot['available_slots'],
#             'total_slots': slot['total_slots']
#         })
    
#     conn.close()
#     return jsonify(predictions)

# if __name__ == '__main__':
#     app.run(debug=True)

# app.py (Flask backend)
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database initialization - USING CORRECT TABLE NAMES
def init_db():
    conn = sqlite3.connect('pilgrim.db')
    c = conn.cursor()

    # Drop old tables (for development safety) - USING CORRECT NAMES
    c.execute('DROP TABLE IF EXISTS admins')
    c.execute('DROP TABLE IF EXISTS time_slots')
    c.execute('DROP TABLE IF EXISTS bookings')
    c.execute('DROP TABLE IF EXISTS incidents')
    # DON'T drop: users, visitors, volunteers, historical_data, etc.

    # Then create only the admin tables you need
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            temple_name TEXT NOT NULL
        )
    ''')

    # Time_slots table
    c.execute('''
        CREATE TABLE time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temple_name TEXT,
            date TEXT,
            slot_time TEXT,
            capacity INTEGER,
            booked INTEGER DEFAULT 0
        )
    ''')

    # Bookings table
    c.execute('''
        CREATE TABLE bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            temple_name TEXT,
            slot_id INTEGER,
            booking_time TEXT,
            qr_code TEXT,
            entry_time TEXT,
            exit_time TEXT,
            status TEXT DEFAULT 'confirmed'
        )
    ''')

    # Incidents table
    c.execute('''
        CREATE TABLE incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            temple_name TEXT,
            description TEXT,
            timestamp TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Visitors table (for emergencies)
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            temple_name TEXT,
            emergency_type TEXT,
            location TEXT,
            timestamp TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Insert sample data
    c.execute('''
        INSERT INTO admins (username, password_hash, temple_name) 
        VALUES (?, ?, ?)
    ''', ('admin', 'password123', 'Sample Temple'))

    # Insert sample time slots
    today = datetime.now().strftime('%Y-%m-%d')
    time_slots = ['06:00-08:00', '08:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00', '16:00-18:00']
    
    for slot_time in time_slots:
        c.execute('''
            INSERT INTO time_slots (temple_name, date, slot_time, capacity, booked) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('Sample Temple', today, slot_time, 200, 0))

    conn.commit()
    conn.close()

init_db()

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect('pilgrim.db')
    conn.row_factory = sqlite3.Row
    return conn

# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin and password == admin['password_hash']:
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            session['admin_temple'] = admin['temple_name']
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    
    return render_template('admin_login.html')

# Admin dashboard - UPDATED WITH CORRECT TABLE NAMES
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    temple_name = session.get('admin_temple', 'Sample Temple')
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db()
    
    # Get today's slots - UPDATED to use time_slots table
    slots = conn.execute('''SELECT * FROM time_slots 
                          WHERE temple_name = ? AND date = ? 
                          ORDER BY slot_time''', (temple_name, today)).fetchall()
    
    # Get recent emergencies - UPDATED to use visitors table
    emergencies = conn.execute('''SELECT * FROM visitors 
                                WHERE temple_name = ? 
                                ORDER BY timestamp DESC LIMIT 5''', (temple_name,)).fetchall()
    
    # Get recent incidents
    incidents = conn.execute('''SELECT * FROM incidents 
                              WHERE temple_name = ? 
                              ORDER BY timestamp DESC LIMIT 5''', (temple_name,)).fetchall()
    
    # Get current crowd data
    current_time = datetime.now().time()
    current_slot = None
    
    for slot in slots:
        start_time, end_time = slot['slot_time'].split('-')
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        
        slot_start = datetime.now().replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        slot_end = datetime.now().replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        
        if slot_start.time() <= current_time <= slot_end.time():
            current_slot = slot
            break
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         temple_name=temple_name, 
                         slots=slots, 
                         emergencies=emergencies, 
                         incidents=incidents,
                         current_slot=current_slot,
                         today=today)

# API to get slot details - UPDATED
@app.route('/admin/api/slots/<date>')
def get_slots(date):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    temple_name = session.get('admin_temple', 'Sample Temple')
    
    conn = get_db()
    slots = conn.execute('''SELECT * FROM time_slots 
                          WHERE temple_name = ? AND date = ? 
                          ORDER BY slot_time''', (temple_name, date)).fetchall()
    
    result = []
    for slot in slots:
        result.append(dict(slot))
    
    conn.close()
    return jsonify(result)

# API to update slot capacity - UPDATED
@app.route('/admin/api/slots/update', methods=['POST'])
def update_slot():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    data = request.json
    slot_id = data.get('slot_id')
    capacity = data.get('capacity')
    
    conn = get_db()
    conn.execute('UPDATE time_slots SET capacity = ? WHERE id = ?', (capacity, slot_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API to get emergency details - UPDATED
@app.route('/admin/api/emergencies')
def get_emergencies():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    temple_name = session.get('admin_temple', 'Sample Temple')
    
    conn = get_db()
    emergencies = conn.execute('''SELECT * FROM visitors 
                                WHERE temple_name = ? 
                                ORDER BY timestamp DESC''', (temple_name,)).fetchall()
    
    result = []
    for emergency in emergencies:
        result.append(dict(emergency))
    
    conn.close()
    return jsonify(result)

# API to update emergency status - UPDATED
@app.route('/admin/api/emergencies/update', methods=['POST'])
def update_emergency():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    data = request.json
    emergency_id = data.get('emergency_id')
    status = data.get('status')
    
    conn = get_db()
    conn.execute('UPDATE visitors SET status = ? WHERE id = ?', (status, emergency_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API to get incidents
@app.route('/admin/api/incidents')
def get_incidents():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    temple_name = session.get('admin_temple', 'Sample Temple')
    
    conn = get_db()
    incidents = conn.execute('''SELECT * FROM incidents 
                              WHERE temple_name = ? 
                              ORDER BY timestamp DESC''', (temple_name,)).fetchall()
    
    result = []
    for incident in incidents:
        result.append(dict(incident))
    
    conn.close()
    return jsonify(result)

# API to update incident status
@app.route('/admin/api/incidents/update', methods=['POST'])
def update_incident():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    data = request.json
    incident_id = data.get('incident_id')
    status = data.get('status')
    
    conn = get_db()
    conn.execute('UPDATE incidents SET status = ? WHERE id = ?', (status, incident_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)