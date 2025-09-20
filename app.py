# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import check_password_hash   # ✅ Needed for admin login
from database import init_db    
import crowd_prediction
import json
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

from werkzeug.security import generate_password_hash
from functools import wraps

                

app = Flask(__name__)
app.secret_key = 'pilgrim_secret_key'

# ✅ Initialize DB at startup
init_db()


# ✅ Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "your_email@gmail.com"
app.config['MAIL_PASSWORD'] = "your_app_password"
app.config['MAIL_DEFAULT_SENDER'] = "your_email@gmail.com"

mail = Mail(app)

# ✅ Scheduler jobs now receive mail object
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: notify_expiring_bookings(), trigger="interval", minutes=5)
scheduler.add_job(func=lambda: notify_extreme_crowd(), trigger="interval", hours=1)
scheduler.start()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Admin access required", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


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
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, datetime.now().isoformat()))
            conn.commit()
            flash("✅ Registration successful! Please login.", "success")
            return redirect(url_for('index'))  # redirect to login page
        except sqlite3.IntegrityError:
            flash("❌ Username or Email already exists!", "error")
            return redirect(url_for('user_register'))
        finally:
            conn.close()

    # GET request: show registration form
    return render_template('register.html')

@app.route('/user/login', methods=['POST'])
def user_login():
    identifier = request.form.get('username')  # could be username or email
    password = request.form.get('password')

    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Query either by username or email
    cursor.execute('''
        SELECT id, username, password_hash, email 
        FROM users 
        WHERE username = ? OR email = ?
    ''', (identifier, identifier))
    
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        # Login successful
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['email'] = user[3]
        flash("✅ Logged in successfully!", "success")
        return redirect(url_for('user_dashboard'))
    else:
        flash("❌ Invalid username/email or password!", "error")
        return redirect(url_for('index'))



@app.route('/user/dashboard')
@login_required
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
                           )




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
@admin_required
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




@app.route("/admin/notifications")
def view_notifications():
    conn = sqlite3.connect("pilgrim.db")
    cursor = conn.cursor()
    cursor.execute("SELECT recipient, subject, status, created_at FROM notifications_log ORDER BY created_at DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template("admin_notifications.html", logs=logs)


@app.route('/visualization')
def visualization():
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

@app.route('/admin/notify', methods=['POST'])
def send_notification():
    subject = request.form.get('subject')
    message_body = request.form.get('message')

    if not subject or not message_body:
        flash("Subject and message cannot be empty!", "error")
        return redirect(url_for('admin_dashboard'))

    try:
        # Fetch all users from DB
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM users')
        users = cursor.fetchall()
        conn.close()

        if not users:
            flash("No users found to notify.", "warning")
            return redirect(url_for('admin_dashboard'))

        success_count, fail_count = 0, 0

        for user in users:
            email = user[0]
            try:
                msg = Message(subject, recipients=[email])
                msg.body = message_body
                mail.send(msg)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send email to {email}: {e}")
                fail_count += 1

        flash(f"✅ Emails sent: {success_count}, ❌ Failed: {fail_count}", "success")

    except Exception as e:
        logger.error(f"Notification system error: {e}")
        flash("An error occurred while sending notifications.", "error")

    return redirect(url_for('admin_dashboard'))

# @app.route('/test-email')
# def test_email():
#     try:
#         msg = Message("Test Email", recipients=["test_receiver@example.com"])
#         msg.body = "This is a test email from Pilgrim Management System."
#         mail.send(msg)
#         return "✅ Test email sent successfully!"
#     except Exception as e:
#         logger.error(f"Test email failed: {e}")
#         return f"❌ Failed to send test email: {e}"



if __name__ == '__main__':
    app.run(debug=True)