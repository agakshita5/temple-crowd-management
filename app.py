# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import check_password_hash
from database import init_db
# Note: The crowd_prediction import might need adjustment based on your final model's input needs.
# This version assumes the simple prediction model for now.
# import crowd_prediction 
from werkzeug.security import generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'pilgrim_secret_key'

init_db()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Admin access required", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Main Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

# --- User Authentication ---
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username or not email or not password:
            flash("All fields are required!", "error")
            return redirect(url_for('user_register'))
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                           (username, email, password_hash, datetime.now().isoformat()))
            conn.commit()
            flash("✅ Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("❌ Username or Email already exists!", "error")
            return redirect(url_for('user_register'))
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/user/login', methods=['POST'])
def user_login():
    identifier = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, email FROM users WHERE username = ? OR email = ?',
                   (identifier, identifier))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[2], password):
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['email'] = user[3]
        flash(f"✅ Welcome back, {user[1]}!", "success")
        return redirect(url_for('user_dashboard'))
    else:
        flash("❌ Invalid username/email or password!", "error")
        return redirect(url_for('login'))

# --- User Dashboard and Features ---
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/book')
@login_required
def book_slot_page():
    today = datetime.now()
    temple_name = "Somnath" # Example temple
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, slot_time, (capacity - booked) as available_slots FROM time_slots 
        WHERE date = ? AND temple_name = ? AND (capacity - booked) > 0
        ORDER BY slot_time
    ''', (today.date().isoformat(), temple_name))
    slots = cursor.fetchall()
    conn.close()
    return render_template('book_slot.html',
                           username=session['username'],
                           slots=slots,
                           temple_name=temple_name)

@app.route('/my_bookings')
@login_required
def my_bookings():
    user_id = session['user_id']
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    # This query now correctly includes the 'status' column
    cursor.execute('''
        SELECT b.id, b.qr_code, t.date, t.slot_time, t.temple_name, b.status
        FROM bookings b
        JOIN time_slots t ON b.slot_id = t.id
        WHERE b.user_id = ?
        ORDER BY t.date DESC, t.slot_time DESC
    ''', (user_id,))
    bookings = cursor.fetchall()
    conn.close()
    # The page name was changed from my_bookings to my_entry_pass, so we render that instead
    return render_template('my_bookings.html', bookings=bookings)

# --- NEW ROUTES FOR DASHBOARD FEATURES ---
@app.route('/live_crowd')
@login_required
def live_crowd():
    # Using placeholder data for live crowd status
    crowd_levels = ['Low', 'Moderate', 'High']
    crowd_status = {
        'Somnath': random.choice(crowd_levels),
        'Dwarka': random.choice(crowd_levels),
        'Ambaji': random.choice(crowd_levels),
        'Pavagadh': random.choice(crowd_levels)
    }
    last_updated = datetime.now().strftime("%I:%M %p")
    return render_template('live_crowd.html', crowd_status=crowd_status, last_updated=last_updated)

@app.route('/donation')
@login_required
def donation():
    return render_template('donation.html')

@app.route('/report_incident')
@login_required
def report_incident():
    return render_template('report_incident.html')

@app.route('/emergency_contacts')
@login_required
def emergency_contacts():
    return render_template('emergency_contacts.html')
# --- END OF NEW ROUTES ---

@app.route('/book/slot', methods=['POST'])
@login_required
def book_slot_action():
    slot_id = request.form.get('slot_id')
    user_id = session['user_id']
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT available_slots FROM time_slots WHERE id = ?', (slot_id,))
    result = cursor.fetchone()
    if not result or result[0] <= 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Slot no longer available'})
    booking_id = random.randint(100000, 999999)
    qr_code_data = f'BOOKING-{booking_id}-USER-{user_id}-SLOT-{slot_id}'
    cursor.execute('''
        INSERT INTO bookings (user_id, slot_id, qr_code, booking_time, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, slot_id, qr_code_data, datetime.now().isoformat(), 'confirmed'))
    cursor.execute('UPDATE time_slots SET booked = booked + 1 WHERE id = ?', (slot_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Booking successful!', 'booking_id': booking_id, 'qr_code': qr_code_data})

# --- Admin Section ---
@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash FROM admins WHERE username = ?', (username,))
    admin = cursor.fetchone()
    conn.close()
    if admin and check_password_hash(admin[2], password):
        session['admin_id'] = admin[0]
        session['admin_user'] = admin[1]
        flash('Welcome, Admin!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid admin credentials', 'error')
        return redirect(url_for('login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    predictions = []
    temple_name = "Somnath"
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        # Using a simplified random prediction for the admin dashboard view
        prediction = random.randint(5000, 50000)
        predictions.append({'date': date.date(), 'prediction': prediction})

    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.booking_id, b.booking_time, t.slot_date, t.slot_time, t.temple_name 
        FROM bookings b JOIN time_slots t ON b.slot_id = t.id
        ORDER BY b.booking_time DESC LIMIT 10
    ''')
    recent_bookings = cursor.fetchall()
    conn.close()
    return render_template('admin.html', predictions=predictions, recent_bookings=recent_bookings, temple_name=temple_name)

@app.route('/visualization')
@admin_required
def visualization():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, temple_name, estimated_footfall FROM historical_data LIMIT 30')
    historical_data = cursor.fetchall()
    conn.close()
    return render_template('visualization.html', historical_data=historical_data)


if __name__ == '__main__':
    app.run(debug=True)

