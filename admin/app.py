# app.py (Flask backend)
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database initialization
def init_db():
    conn = sqlite3.connect('temple_management.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS temples
                 (id INTEGER PRIMARY KEY, name TEXT, location TEXT, capacity INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS slots
                 (id INTEGER PRIMARY KEY, temple_id INTEGER, date TEXT, 
                 slot_time TEXT, capacity INTEGER, booked INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY, user_id INTEGER, temple_id INTEGER, 
                 slot_id INTEGER, booking_time TEXT, qr_code TEXT, 
                 entry_time TEXT, exit_time TEXT, status TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS emergencies
                 (id INTEGER PRIMARY KEY, user_id INTEGER, temple_id INTEGER, 
                 emergency_type TEXT, location TEXT, timestamp TEXT, status TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS incidents
                 (id INTEGER PRIMARY KEY, user_id INTEGER, temple_id INTEGER, 
                 description TEXT, timestamp TEXT, status TEXT)''')
    
    # Insert sample data if needed
    c.execute("SELECT COUNT(*) FROM temples")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO temples (name, location, capacity) VALUES (?, ?, ?)", 
                 ('Somnath Temple', 'Veraval, Gujarat', 10000))
        c.execute("INSERT INTO temples (name, location, capacity) VALUES (?, ?, ?)", 
                 ('Dwarkadhish Temple', 'Dwarka, Gujarat', 8000))
    
    conn.commit()
    conn.close()

init_db()

# Helper function to get database connection
def get_db():
    conn = sqlite3.connect('temple_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# Admin login route (simplified for demo)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple authentication (in real app, use proper authentication)
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_temple'] = request.form.get('temple', '1')  # Default to first temple
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    temple_id = session.get('admin_temple', 1)
    
    # Get temple details
    conn = get_db()
    temple = conn.execute('SELECT * FROM temples WHERE id = ?', (temple_id,)).fetchone()
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get today's slots
    slots = conn.execute('''SELECT * FROM slots 
                          WHERE temple_id = ? AND date = ? 
                          ORDER BY slot_time''', (temple_id, today)).fetchall()
    
    # Get recent emergencies
    emergencies = conn.execute('''SELECT * FROM emergencies 
                                WHERE temple_id = ? 
                                ORDER BY timestamp DESC LIMIT 5''', (temple_id,)).fetchall()
    
    # Get recent incidents
    incidents = conn.execute('''SELECT * FROM incidents 
                              WHERE temple_id = ? 
                              ORDER BY timestamp DESC LIMIT 5''', (temple_id,)).fetchall()
    
    # Get current crowd data (simulated)
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
                         temple=temple, 
                         slots=slots, 
                         emergencies=emergencies, 
                         incidents=incidents,
                         current_slot=current_slot,
                         today=today)

# API to get slot details
@app.route('/admin/api/slots/<date>')
def get_slots(date):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    temple_id = session.get('admin_temple', 1)
    
    conn = get_db()
    slots = conn.execute('''SELECT * FROM slots 
                          WHERE temple_id = ? AND date = ? 
                          ORDER BY slot_time''', (temple_id, date)).fetchall()
    
    result = []
    for slot in slots:
        result.append(dict(slot))
    
    conn.close()
    return jsonify(result)

# API to update slot capacity
@app.route('/admin/api/slots/update', methods=['POST'])
def update_slot():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    data = request.json
    slot_id = data.get('slot_id')
    capacity = data.get('capacity')
    
    conn = get_db()
    conn.execute('UPDATE slots SET capacity = ? WHERE id = ?', (capacity, slot_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API to get emergency details
@app.route('/admin/api/emergencies')
def get_emergencies():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    temple_id = session.get('admin_temple', 1)
    
    conn = get_db()
    emergencies = conn.execute('''SELECT * FROM emergencies 
                                WHERE temple_id = ? 
                                ORDER BY timestamp DESC''', (temple_id,)).fetchall()
    
    result = []
    for emergency in emergencies:
        result.append(dict(emergency))
    
    conn.close()
    return jsonify(result)

# API to update emergency status
@app.route('/admin/api/emergencies/update', methods=['POST'])
def update_emergency():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    data = request.json
    emergency_id = data.get('emergency_id')
    status = data.get('status')
    
    conn = get_db()
    conn.execute('UPDATE emergencies SET status = ? WHERE id = ?', (status, emergency_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API to get incidents
@app.route('/admin/api/incidents')
def get_incidents():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Not authorized'}), 401
    
    temple_id = session.get('admin_temple', 1)
    
    conn = get_db()
    incidents = conn.execute('''SELECT * FROM incidents 
                              WHERE temple_id = ? 
                              ORDER BY timestamp DESC''', (temple_id,)).fetchall()
    
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