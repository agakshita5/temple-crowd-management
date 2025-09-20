# # app.py
# from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
# import sqlite3
# from datetime import datetime, timedelta
# import random
# from werkzeug.security import check_password_hash   # ✅ Needed for admin login
# from database import init_db                        # ✅ Use init_db from database.py

# app = Flask(__name__)
# app.secret_key = 'pilgrim_secret_key'

# # ✅ Initialize DB at startup
# init_db()

# # --- Crowd Prediction Function ---
# def predict_crowd(date, temple_name):
#     day_of_week = date.weekday()  # 0=Monday, 6=Sunday
#     is_weekend = 1 if day_of_week >= 5 else 0
#     month = date.month

#     holidays = [
#         (1, 1), (1, 14), (3, 8), (8, 15), (10, 2), (12, 25)
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
#     variation = random.uniform(0.9, 1.1)
#     return int(predicted_crowd * variation)

# # --- Routes ---
# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/user/login', methods=['POST'])
# def user_login():
#     username = request.form.get('username')
#     session['user_id'] = 1
#     session['username'] = username
#     return redirect(url_for('user_dashboard'))

# @app.route('/user/dashboard')
# def user_dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('index'))

#     today = datetime.now()
#     temple_name = "Somnath"
#     prediction = predict_crowd(today, temple_name)

#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT id, slot_time, available_slots FROM time_slots 
#         WHERE slot_date = ? AND temple_name = ? AND available_slots > 0
#         ORDER BY slot_time
#     ''', (today.date(), temple_name))
#     slots = cursor.fetchall()
#     conn.close()

#     return render_template('user_dashboard.html',
#                            username=session['username'],
#                            prediction=prediction,
#                            slots=slots,
#                            temple_name=temple_name)

# @app.route('/book/slot', methods=['POST'])
# def book_slot():
#     if 'user_id' not in session:
#         return jsonify({'success': False, 'message': 'Please login first'})

#     slot_id = request.form.get('slot_id')
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()

#     cursor.execute('SELECT available_slots FROM time_slots WHERE id = ?', (slot_id,))
#     result = cursor.fetchone()

#     if not result or result[0] <= 0:
#         conn.close()
#         return jsonify({'success': False, 'message': 'Slot no longer available'})

#     booking_id = random.randint(100000, 999999)
#     cursor.execute('UPDATE time_slots SET available_slots = available_slots - 1 WHERE id = ?', (slot_id,))
#     cursor.execute('''
#         INSERT INTO bookings (user_id, slot_id, booking_id, qr_code, booking_time)
#         VALUES (?, ?, ?, ?, ?)
#     ''', (session['user_id'], slot_id, booking_id, f'QR_{booking_id}', datetime.now()))

#     conn.commit()
#     conn.close()

#     return jsonify({
#         'success': True,
#         'message': 'Slot booked successfully!',
#         'booking_id': booking_id,
#         'qr_code': f'QR_{booking_id}'
#     })

# @app.route('/admin/login', methods=['POST'])
# def admin_login():
#     username = request.form.get('username')
#     password = request.form.get('password')

#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT id, username, password_hash FROM admins WHERE username = ?', (username,))
#     admin = cursor.fetchone()
#     conn.close()

#     if admin and check_password_hash(admin[2], password):
#         session['admin_id'] = admin[0]
#         session['admin_user'] = admin[1]
#         flash('Welcome, Admin!', 'success')
#         return redirect(url_for('admin_dashboard'))
#     else:
#         flash('Invalid admin credentials', 'error')
#         return redirect(url_for('index'))

# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if 'admin_id' not in session:
#         return redirect(url_for('index'))

#     predictions = []
#     temple_name = "Somnath"
#     for i in range(7):
#         date = datetime.now() + timedelta(days=i)
#         prediction = predict_crowd(date, temple_name)
#         predictions.append({'date': date.date(), 'prediction': prediction})

#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT b.booking_id, b.booking_time, t.slot_date, t.slot_time, t.temple_name 
#         FROM bookings b
#         JOIN time_slots t ON b.slot_id = t.id
#         ORDER BY b.booking_time DESC
#         LIMIT 10
#     ''')
#     recent_bookings = cursor.fetchall()
#     conn.close()

#     return render_template('admin.html',
#                            predictions=predictions,
#                            recent_bookings=recent_bookings,
#                            temple_name=temple_name)

# @app.route('/visualization')
# def visualization():
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT date, temple_name, estimated_footfall FROM historical_data LIMIT 30')
#     historical_data = cursor.fetchall()
#     conn.close()
#     return render_template('visualization.html', historical_data=historical_data)

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run(debug=True)


# from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
# import sqlite3
# from datetime import datetime, timedelta
# import random
# from werkzeug.security import check_password_hash, generate_password_hash
# import crowd_prediction

# app = Flask(__name__)
# app.secret_key = 'pilgrim_secret_key'

# # Initialize database
# import database
# database.init_db()

# # Routes
# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/user/login', methods=['POST'])
# def user_login():
#     username = request.form.get('username')
#     session['user_id'] = 1
#     session['username'] = username
#     return redirect(url_for('user_dashboard'))

# @app.route('/user/dashboard')
# def user_dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('index'))

#     today = datetime.now()
#     temple_name = "Somnath"
    
#     # Get crowd prediction for today
#     prediction = crowd_prediction.predict_crowd(today, temple_name)
    
#     # Get available slots
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT id, slot_time, available_slots FROM time_slots 
#         WHERE slot_date = ? AND temple_name = ? AND available_slots > 0
#         ORDER BY slot_time
#     ''', (today.date(), temple_name))
#     slots = cursor.fetchall()
#     conn.close()

#     return render_template('user_dashboard.html',
#                            username=session['username'],
#                            prediction=prediction,
#                            slots=slots,
#                            temple_name=temple_name)

# @app.route('/book/slot', methods=['POST'])
# def book_slot():
#     if 'user_id' not in session:
#         return jsonify({'success': False, 'message': 'Please login first'})

#     slot_id = request.form.get('slot_id')
#     persons = request.form.get('persons', 1)
    
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()

#     cursor.execute('SELECT available_slots FROM time_slots WHERE id = ?', (slot_id,))
#     result = cursor.fetchone()

#     if not result or result[0] <= 0:
#         conn.close()
#         return jsonify({'success': False, 'message': 'Slot no longer available'})

#     # Update available slots
#     cursor.execute('UPDATE time_slots SET available_slots = available_slots - ? WHERE id = ?', 
#                   (persons, slot_id))
    
#     # Create booking
#     booking_id = random.randint(100000, 999999)
#     cursor.execute('''
#         INSERT INTO bookings (user_id, slot_id, persons, booking_id, qr_code, booking_time)
#         VALUES (?, ?, ?, ?, ?, ?)
#     ''', (session['user_id'], slot_id, persons, booking_id, f'QR_{booking_id}', datetime.now()))

#     conn.commit()
#     conn.close()

#     return jsonify({
#         'success': True,
#         'message': 'Slot booked successfully!',
#         'booking_id': booking_id,
#         'qr_code': f'QR_{booking_id}'
#     })

# @app.route('/admin/login', methods=['POST'])
# def admin_login():
#     username = request.form.get('username')
#     password = request.form.get('password')

#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT id, username, password_hash FROM admins WHERE username = ?', (username,))
#     admin = cursor.fetchone()
#     conn.close()

#     if admin and check_password_hash(admin[2], password):
#         session['admin_id'] = admin[0]
#         session['admin_user'] = admin[1]
#         flash('Welcome, Admin!', 'success')
#         return redirect(url_for('admin_dashboard'))
#     else:
#         flash('Invalid admin credentials', 'error')
#         return redirect(url_for('index'))

# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if 'admin_id' not in session:
#         return redirect(url_for('index'))

#     # Generate 7-day predictions
#     predictions = []
#     temple_name = "Somnath"
#     for i in range(7):
#         date = datetime.now() + timedelta(days=i)
#         prediction = crowd_prediction.predict_crowd(date, temple_name)
#         predictions.append({'date': date.date(), 'prediction': prediction})

#     # Get recent bookings
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT b.booking_id, b.booking_time, t.slot_date, t.slot_time, t.temple_name 
#         FROM bookings b
#         JOIN time_slots t ON b.slot_id = t.id
#         ORDER BY b.booking_time DESC
#         LIMIT 10
#     ''')
#     recent_bookings = cursor.fetchall()
#     conn.close()

#     return render_template('admin.html',
#                            predictions=predictions,
#                            recent_bookings=recent_bookings,
#                            temple_name=temple_name)

# @app.route('/visualization')
# def visualization():
#     # Get historical data for visualization
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT date, temple_name, estimated_footfall FROM historical_data LIMIT 30')
#     historical_data = cursor.fetchall()
#     conn.close()
    
#     return render_template('visualization.html', historical_data=historical_data)

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run(debug=True)



from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import check_password_hash, generate_password_hash
import crowd_prediction
import requests
import json
import razorpay
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = 'pilgrim_secret_key'

# Initialize database
import database
database.init_db()

# Payment Gateway Configuration (Razorpay for example)
RAZORPAY_KEY_ID = 'your_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'

# Razorpay keys (from dashboard)
razorpay_client = razorpay.Client(auth=("YOUR_KEY_ID", "YOUR_KEY_SECRET"))

@app.route("/create_order", methods=["POST"])
def create_order():
    data = request.json
    amount = int(data["amount"]) * 100  # in paise
    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })
    return jsonify(order)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/login', methods=['POST'])
def user_login():
    username = request.form.get('username')
    session['user_id'] = 1
    session['username'] = username
    return redirect(url_for('user_dashboard'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    today = datetime.now()
    temple_name = "Somnath"
    
    # Get crowd prediction for today
    prediction = crowd_prediction.predict_crowd(today, temple_name)
    
    # Get available slots
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, slot_time, available_slots FROM time_slots 
        WHERE slot_date = ? AND temple_name = ? AND available_slots > 0
        ORDER BY slot_time
    ''', (today.date(), temple_name))
    slots = cursor.fetchall()
    conn.close()

    return render_template('user_dashboard.html',
                           username=session['username'],
                           prediction=prediction,
                           slots=slots,
                           temple_name=temple_name,
                           razorpay_key=RAZORPAY_KEY_ID)

@app.route('/book/slot', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    slot_id = request.form.get('slot_id')
    persons = request.form.get('persons', 1)
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()

    cursor.execute('SELECT available_slots FROM time_slots WHERE id = ?', (slot_id,))
    result = cursor.fetchone()

    if not result or result[0] <= 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Slot no longer available'})

    # Create booking first (will be confirmed after payment)
    booking_id = random.randint(100000, 999999)
    cursor.execute('''
        INSERT INTO bookings (user_id, slot_id, persons, booking_id, qr_code, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], slot_id, persons, booking_id, f'QR_{booking_id}', datetime.now(), 'pending'))
    
    booking_db_id = cursor.lastrowid
    
    conn.commit()
    conn.close()

    # Create payment order
    amount = int(persons) * 50 * 100  # Amount in paisa
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': f'booking_{booking_id}',
        'notes': {
            'booking_id': booking_id,
            'user_id': session['user_id'],
            'slot_id': slot_id
        }
    }
    
    # In a real implementation, you would create a Razorpay order here
    # For demo purposes, we'll simulate it
    order_id = f'order_{random.randint(100000, 999999)}'
    
    return jsonify({
        'success': True,
        'message': 'Please proceed to payment',
        'booking_id': booking_id,
        'order_id': order_id,
        'amount': amount,
        'name': 'Temple Darshan Booking',
        'email': session.get('email', ''),
        'contact': session.get('phone', '')
    })

@app.route('/payment/verify', methods=['POST'])
def verify_payment():
    data = request.json
    payment_id = data.get('payment_id')
    order_id = data.get('order_id')
    signature = data.get('signature')
    booking_id = data.get('booking_id')
    
    # In a real implementation, you would verify the payment signature with Razorpay
    # For demo purposes, we'll assume payment is successful
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Update booking status to confirmed
    cursor.execute('UPDATE bookings SET status = ? WHERE booking_id = ?', ('confirmed', booking_id))
    
    # Update available slots
    cursor.execute('''
        UPDATE time_slots SET available_slots = available_slots - 
        (SELECT persons FROM bookings WHERE booking_id = ?) 
        WHERE id = (SELECT slot_id FROM bookings WHERE booking_id = ?)
    ''', (booking_id, booking_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Payment verified successfully',
        'qr_code': f'QR_{booking_id}'
    })

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
        return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('index'))

    # Generate 7-day predictions
    predictions = []
    temple_name = "Somnath"
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        prediction = crowd_prediction.predict_crowd(date, temple_name)
        predictions.append({'date': date.date(), 'prediction': prediction})

    # Get recent bookings
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.booking_id, b.booking_time, t.slot_date, t.slot_time, t.temple_name 
        FROM bookings b
        JOIN time_slots t ON b.slot_id = t.id
        ORDER BY b.booking_time DESC
        LIMIT 10
    ''')
    recent_bookings = cursor.fetchall()
    conn.close()

    return render_template('admin.html',
                           predictions=predictions,
                           recent_bookings=recent_bookings,
                           temple_name=temple_name)

@app.route('/visualization')
def visualization():
    # Get historical data for visualization
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, temple_name, estimated_footfall FROM historical_data LIMIT 30')
    historical_data = cursor.fetchall()
    conn.close()
    
    return render_template('visualization.html', historical_data=historical_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)