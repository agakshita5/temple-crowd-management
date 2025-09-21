# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
import sqlite3
from datetime import datetime, timedelta,time
import random
from werkzeug.security import check_password_hash , generate_password_hash  # ✅ Needed for admin login
from database import init_db    
import crowd_prediction
import json
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin

from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from functools import wraps
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from werkzeug.utils import secure_filename
import stripe
                

app = Flask(__name__)
app.secret_key = 'pilgrim_secret_key'

stripe.api_key = "sk_test_51RFY3IQW8fY5qAnlngq7SziCL1ypMXcLcbiVu0FOQmkkGseDB6wfosb1EoAriqioM8ykZYWmxD2hMYrjAvK4jyxT00nARclhw4"
STRIPE_PUBLISHABLE_KEY = "pk_test_51RFY3IQW8fY5qAnl73PdcNdfIovzFy8mzDHMpWMqSkaiLdq9s2cTQT7JEHfrhUHYL5C16SAXsAJFn7039pPYikvV00aW0yg2Mi"

UPI_ID = "7014080430@axl"
PAYEE_NAME = "Sonam Yadav"
# ✅ Add file upload configuration here
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ Initialize DB at startup
init_db()


@app.route('/send_qr_email', methods=['POST'])
@login_required
def send_qr_email():
    data = request.json
    booking_id = data.get('booking_id')
    qr_data = data.get('qr_data')  # The text encoded in the QR

    msg = Message(
        subject=f"Your Pilgrim Booking QR: {booking_id}",
        recipients=[session.get('email')]
    )
    msg.body = f"Dear {session.get('username')},\n\nHere is your QR ticket for booking ID {booking_id}:\n\n{qr_data}\n\nPlease show this QR at the temple."
    
    try:
        mail.send(msg)
        return jsonify({"success": True, "message": "Email sent successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For AJAX, return JSON instead of redirect
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "message": "Login required"}), 401
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


# Routes
@app.route('/')
def home():
    return render_template('home.html')  # Changed from index.html to home.html

@app.route('/index')
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

@app.route('/login')
def login_page():
    return render_template('login.html')  # Create this template if it doesn't exist

# # Keep your existing POST route but update the endpoint
# @app.route('/login', methods=['POST'])
# def user_login():
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
        return redirect(url_for('welcome'))
    else:
        flash("❌ Invalid username/email or password!", "error")
        return redirect(url_for('index'))  # Redirect back to login page

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
        return redirect(url_for('welcome'))
    else:
        flash("❌ Invalid username/email or password!", "error")
        return redirect(url_for('login'))

@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        # You can process form data or directly redirect
        return redirect(url_for('user_dashboard'))
    return render_template('welcome.html')

@app.route('/live_crowd')
def live_crowd():
    # Your implementation here
    return render_template('live_crowd.html')

@app.route('/emergency_contacts')
def emergency_contacts():
    # Add your emergency contacts logic here
    return render_template('emergency_contacts.html')

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    today = datetime.now()
    temple_name = "Somnath"
    
    prediction = crowd_prediction.predict_crowd(today, temple_name)
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()

    # 🔹 get available slots
    cursor.execute('''
        SELECT id, slot_time, available_slots FROM time_slots 
        WHERE slot_date = ? AND temple_name = ? AND available_slots > 0
        ORDER BY slot_time
    ''', (today.date(), temple_name))
    slots = cursor.fetchall()

    # 🔹 get latest booking for current user (joining time_slots for details)
    cursor.execute('''
        SELECT b.id, t.temple_name, t.slot_time, t.slot_date
        FROM bookings b
        JOIN time_slots t ON b.slot_id = t.id
        WHERE b.user_id = ?
        ORDER BY t.slot_date DESC, t.slot_time DESC
        LIMIT 1
    ''', (session['user_id'],))
    booking_data = cursor.fetchone()
    
    conn.close()

    # Format date for display
    date_today = today.strftime("%B %d, %Y")

    return render_template(
        'user_dashboard.html',
        username=session['username'],
        prediction=prediction,
        slots=slots,
        temple_name=temple_name,
        booking_data=booking_data,
        date_today=date_today  # Add the formatted date
    )
@app.route('/my-account')
@login_required
def my_account():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Get user details
    cursor.execute('SELECT username, email, created_at FROM users WHERE id = ?', (session['user_id'],))
    user_data = cursor.fetchone()
    
    # Get booking count
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE user_id = ?', (session['user_id'],))
    booking_count = cursor.fetchone()[0]
    
    # Get visitor count
    cursor.execute('SELECT COUNT(*) FROM visitors WHERE user_id = ?', (session['user_id'],))
    visitor_count = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('my_account.html', 
                         user_data=user_data, 
                         booking_count=booking_count,
                         visitor_count=visitor_count)


@app.route('/book/slot', methods=['POST'])
@login_required
def book_slot():
    try:
        # Get form data
        slot_id = request.form.get('slot_id')
        persons = int(request.form.get('persons', 1))
        
        # Get visitor info from form
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        address = request.form.get('address')
        
        print(f"DEBUG: User ID in session: {session['user_id']}")
        print(f"DEBUG: Form data - Name: {full_name}, Age: {age}, Phone: {phone_number}, Email: {email}")
        print(f"DEBUG: Slot ID: {slot_id}, Persons: {persons}")

        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()

        # Check slot availability
        cursor.execute('SELECT available_slots, slot_time, slot_date, temple_name FROM time_slots WHERE id = ?', (slot_id,))
        slot_data = cursor.fetchone()
        
        if not slot_data:
            conn.close()
            flash('Slot not found', 'error')
            return redirect(url_for('user_dashboard'))
            
        available_slots, slot_time, slot_date, temple_name = slot_data
        
        if available_slots < persons:
            conn.close()
            flash('Not enough slots available for the requested number of persons', 'error')
            return redirect(url_for('user_dashboard'))

        # Create booking with a unique booking ID
        booking_id = random.randint(100000, 999999)
        
        cursor.execute('''
            INSERT INTO bookings (user_id, slot_id, booking_id, qr_code, booking_time, status, persons)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], slot_id, booking_id, f'QR_{booking_id}', datetime.now(), 'confirmed', persons))
        
        booking_db_id = cursor.lastrowid  # Get the actual database ID of the booking
        print(f"DEBUG: Booking created with DB ID: {booking_db_id}, Booking ID: {booking_id}")

        # Insert visitor info - use the database booking ID (booking_db_id), not the display booking ID
        cursor.execute('''
            INSERT INTO visitors (full_name, age, phone_number, email, address, user_id, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, age, phone_number, email, address, session['user_id'], booking_db_id))
        
        print(f"DEBUG: Visitor info inserted for booking DB ID: {booking_db_id}")

        # Update available slots
        cursor.execute('''
            UPDATE time_slots SET available_slots = available_slots - ? WHERE id = ?
        ''', (persons, slot_id))

        conn.commit()
        conn.close()

        flash(f'Booking confirmed for {temple_name} on {slot_date} at {slot_time}! Booking ID: {booking_id}', 'success')
        return redirect(url_for('user_dashboard'))

    except Exception as e:
        print(f"ERROR in book_slot: {str(e)}")
        import traceback
        traceback.print_exc()
        
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('user_dashboard'))
    
@app.route('/select-slot')
@login_required
def select_slot():
    return render_template('select_slot.html')

@app.route('/api/slots', methods=['GET'])
def get_available_slots():
    temple_name = request.args.get('temple', 'Somnath Temple')
    date_str = request.args.get('date')
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'})
    
    conn = sqlite3.connect('pilgrim.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, start_time, end_time, total_slots, available_slots 
        FROM time_slots 
        WHERE temple_name = ? AND slot_date = ? AND is_active = 1 AND available_slots > 0
        ORDER BY start_time
    ''', (temple_name, slot_date))
    
    slots = cursor.fetchall()
    conn.close()
    
    # Format the response
    formatted_slots = []
    for slot in slots:
        formatted_slots.append({
            'id': slot['id'],
            'time_range': f"{slot['start_time']} - {slot['end_time']}",
            'available': slot['available_slots'],
            'total': slot['total_slots'],
            'display_text': f"{slot['start_time']} - {slot['end_time']}<br>{slot['available_slots']} of {slot['total_slots']} slots available"
        })
    
    return jsonify({'success': True, 'slots': formatted_slots})

@app.route('/select-time-slot', methods=['GET', 'POST'])
@login_required
def select_time_slot():
    if request.method == 'GET':
        # Default to today's date and Somnath temple
        slot_date = datetime.now().date()
        temple_name = "Somnath"
        
        # Get available slots for the default date and temple
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, start_time, end_time, total_slots, available_slots 
            FROM time_slots 
            WHERE temple_name = ? AND slot_date = ? AND is_active = 1 AND available_slots > 0
            ORDER BY start_time
        ''', (temple_name, slot_date.isoformat()))
        
        slots = []
        for row in cursor.fetchall():
            slot_id, start_time, end_time, total_slots, available_slots = row
            slots.append({
                'id': slot_id,
                'time_range': f"{start_time} - {end_time}",
                'available_slots': available_slots,
                'total_slots': total_slots,
                'display_text': f"{available_slots} of {total_slots} slots available"
            })
        
        conn.close()
        
        # Get list of temples for the dropdown
        temples = get_available_temples()
        
        return render_template('select_time_slot.html', 
                             slots=slots, 
                             selected_date=slot_date.isoformat(),
                             selected_temple=temple_name,
                             temples=temples)
    
    else:  # POST request - handle slot booking
        try:
            slot_id = request.form.get('slot_id')
            persons = int(request.form.get('persons', 1))
            
            # Get visitor info from form
            full_name = request.form.get('full_name')
            age = request.form.get('age')
            phone_number = request.form.get('phone_number')
            email = request.form.get('email')
            address = request.form.get('address')
            
            conn = sqlite3.connect('pilgrim.db')
            cursor = conn.cursor()

            # Check slot availability
            cursor.execute('''
                SELECT available_slots, start_time, end_time, slot_date, temple_name 
                FROM time_slots 
                WHERE id = ? AND is_active = 1
            ''', (slot_id,))
            
            slot_data = cursor.fetchone()
            
            if not slot_data:
                conn.close()
                flash('Slot not found', 'error')
                return redirect(url_for('select_time_slot'))
                
            available_slots, start_time, end_time, slot_date, temple_name = slot_data
            
            if available_slots < persons:
                conn.close()
                flash('Not enough slots available for the requested number of persons', 'error')
                return redirect(url_for('select_time_slot'))

            # Create booking with a unique booking ID
            booking_id = f"BK{random.randint(100000, 999999)}"
            booking_time = datetime.now()
            
            # Insert booking
            cursor.execute('''
                INSERT INTO bookings (user_id, slot_id, persons, booking_id, booking_time, 
                                    status, temple_name, slot_time, name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], slot_id, persons, booking_id, booking_time,
                 'confirmed', temple_name, f"{start_time} - {end_time}", session['username']))
            
            booking_db_id = cursor.lastrowid

            # Insert visitor info
            cursor.execute('''
                INSERT INTO visitors (full_name, age, phone_number, email, address, user_id, booking_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, age, phone_number, email, address, session['user_id'], booking_db_id))

            # Update available slots
            cursor.execute('''
                UPDATE time_slots SET available_slots = available_slots - ? WHERE id = ?
            ''', (persons, slot_id))

            conn.commit()
            conn.close()

            flash(f'Booking confirmed for {temple_name} on {slot_date} at {start_time}-{end_time}! Booking ID: {booking_id}', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            print(f"ERROR in slot booking: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('select_time_slot'))

# API endpoint to get available slots for a specific date and temple
@app.route('/api/time-slots', methods=['GET'])
def get_time_slots_api():
    temple_name = request.args.get('temple', 'Somnath')
    date_str = request.args.get('date')
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD.'})
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, start_time, end_time, total_slots, available_slots 
        FROM time_slots 
        WHERE temple_name = ? AND slot_date = ? AND is_active = 1 AND available_slots > 0
        ORDER BY start_time
    ''', (temple_name, slot_date.isoformat()))
    
    slots = []
    for row in cursor.fetchall():
        slot_id, start_time, end_time, total_slots, available_slots = row
        slots.append({
            'id': slot_id,
            'time_range': f"{start_time} - {end_time}",
            'available_slots': available_slots,
            'total_slots': total_slots,
            'display_text': f"{start_time} - {end_time}<br>{available_slots} of {total_slots} slots available"
        })
    
    conn.close()
    
    return jsonify({'success': True, 'slots': slots})

# ----------------- DONATION ROUTES -----------------
@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():
    if request.method == 'POST':
        amount = request.form.get('amount')
        donation_type = request.form.get('donation_type')
        message = request.form.get('message', '')
        payment_method = request.form.get('payment_method', 'stripe')

        if not amount or not donation_type:
            flash("Please fill all required fields", "error")
            return redirect(url_for('donate'))

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Please enter a valid donation amount", "error")
                return redirect(url_for('donate'))
        except ValueError:
            flash("Please enter a valid donation amount", "error")
            return redirect(url_for('donate'))

        # Save donation to database
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO donations (user_id, amount, donation_type, message, payment_method, payment_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], amount, donation_type, message, payment_method, 'pending'))
        
        donation_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Redirect to appropriate payment method
        if payment_method == 'upi':
            return redirect(url_for('donate_upi_qr', donation_id=donation_id))
        else:  # stripe
            return redirect(url_for('process_stripe_payment', donation_id=donation_id))

    return render_template('donate.html', 
                         stripe_key=STRIPE_PUBLISHABLE_KEY,
                         upi_id=UPI_ID)

@app.route('/donate/upi_qr/<int:donation_id>')
@login_required
def donate_upi_qr(donation_id):
    import base64, io, qrcode, sqlite3
    from flask import flash, redirect, url_for, render_template, session

    # Define UPI details
    UPI_ID = "7014080430@axl"
    PAYEE_NAME = "Sonam Yadav"   # Replace with your temple/payee name

    # Fetch donation info
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount, donation_type FROM donations WHERE id = ? AND user_id = ?', 
                   (donation_id, session['user_id']))
    donation = cursor.fetchone()
    conn.close()

    if not donation:
        flash("Donation record not found", "error")
        return redirect(url_for('donate'))

    amount, donation_type = donation

    # Generate UPI link
    upi_link = f"upi://pay?pa={UPI_ID}&pn={PAYEE_NAME}&tn={donation_type} Donation&am={amount}&cu=INR"

    # Generate QR code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    return render_template('upi_qr.html', 
                           donation_id=donation_id,
                           amount=amount,
                           donation_type=donation_type,
                           upi_id=UPI_ID,
                           qr_code=qr_base64)


@app.route('/donate/stripe/<int:donation_id>')
@login_required
def process_stripe_payment(donation_id):
    # Fetch donation info
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount FROM donations WHERE id = ? AND user_id = ?', 
                  (donation_id, session['user_id']))
    donation = cursor.fetchone()
    conn.close()

    if not donation:
        flash("Donation record not found", "error")
        return redirect(url_for('donate'))

    amount = donation[0]

    try:
        # Create PaymentIntent (amount in paise for INR)
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to paise
            currency='inr',
            payment_method_types=['card'],
            metadata={
                'donation_id': donation_id,
                'user_id': session['user_id'],
                'username': session['username']
            },
            description=f"Donation by {session['username']}"
        )
        
        return render_template('stripe_payment.html',
                           client_secret=intent.client_secret,
                           amount=amount,
                           donation_id=donation_id,
                           stripe_key=STRIPE_PUBLISHABLE_KEY)
    
    except Exception as e:
        flash(f"Error creating payment: {str(e)}", "error")
        return redirect(url_for('donate'))

@app.route('/donate/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = "whsec_..."  # Add your webhook secret here

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify(success=False), 400

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        donation_id = payment_intent['metadata'].get('donation_id')
        
        if donation_id:
            # Update donation status
            conn = sqlite3.connect('pilgrim.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE donations 
                SET payment_status = 'paid', stripe_payment_id = ?
                WHERE id = ?
            ''', (payment_intent['id'], donation_id))
            conn.commit()
            conn.close()

    return jsonify(success=True), 200

@app.route('/donate/confirm/<int:donation_id>')
@login_required
def confirm_upi_payment(donation_id):
    # For UPI payments, we rely on manual confirmation after user makes payment
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Verify donation belongs to user
    cursor.execute('SELECT payment_status FROM donations WHERE id = ? AND user_id = ?', 
                  (donation_id, session['user_id']))
    donation = cursor.fetchone()
    
    if not donation:
        flash("Donation not found", "error")
        return redirect(url_for('donate'))
    
    if donation[0] == 'pending':
        cursor.execute('UPDATE donations SET payment_status = ? WHERE id = ?', 
                      ('paid', donation_id))
        conn.commit()
        flash("Thank you for your donation! Payment confirmed successfully.", "success")
    else:
        flash("Payment already confirmed", "info")
    
    conn.close()
    return redirect(url_for('user_dashboard'))

@app.route('/donate/success')
@login_required
def donation_success():
    donation_id = request.args.get('donation_id')
    return render_template('donation_success.html', donation_id=donation_id)

@app.route('/donate/cancel')
@login_required
def donation_cancel():
    donation_id = request.args.get('donation_id')
    
    # Update donation status to cancelled
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE donations SET payment_status = ? WHERE id = ?', 
                  ('cancelled', donation_id))
    conn.commit()
    conn.close()
    
    flash("Payment cancelled", "info")
    return redirect(url_for('donate'))

# Helper function to get available temples
def get_available_temples():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT temple_name FROM time_slots ORDER BY temple_name')
    temples = [row[0] for row in cursor.fetchall()]
    conn.close()
    return temples

# Add this function to initialize time slots with the data from the image
def init_time_slots_from_image():
    """Initialize time slots with the data shown in the image"""
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Clear existing slots for the demo
    cursor.execute('DELETE FROM time_slots WHERE slot_date = ?', (datetime.now().date().isoformat(),))
    
    # Add slots from the image
    slots_data = [
        ("06:00", "07:30", 100, 45),
        ("09:00", "10:30", 150, 75),
        ("07:30", "09:00", 200, 120),
        ("10:30", "12:00", 100, 30)
    ]
    
    for start_time, end_time, total_slots, available_slots in slots_data:
        cursor.execute('''
            INSERT INTO time_slots (temple_name, slot_date, start_time, end_time, total_slots, available_slots)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("Somnath", datetime.now().date().isoformat(), start_time, end_time, total_slots, available_slots))
    
    conn.commit()
    conn.close()
    print("✅ Time slots initialized with data from image")
  

@app.route('/admin/visitors')
@admin_required
def view_visitors():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.*, u.username, b.booking_id 
        FROM visitors v 
        JOIN users u ON v.user_id = u.id 
        JOIN bookings b ON v.booking_id = b.id 
        ORDER BY v.created_at DESC
    ''')
    visitors = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_visitors.html', visitors=visitors)


@app.route('/admin/add_test_visitors')
@admin_required
def add_test_visitors():
    """Add test visitor data for demonstration"""
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Get a user and booking to associate with test data
    cursor.execute('SELECT id FROM users LIMIT 1')
    user = cursor.fetchone()
    
    cursor.execute('SELECT id FROM bookings LIMIT 1')
    booking = cursor.fetchone()
    
    if user and booking:
        user_id = user[0]
        booking_id = booking[0]
        
        # Add some test visitors
        test_visitors = [
            ('Rajesh Kumar', 35, '9876543210', 'rajesh@example.com', 'Ahmedabad, Gujarat', user_id, booking_id),
            ('Priya Shah', 28, '8765432109', 'priya@example.com', 'Vadodara, Gujarat', user_id, booking_id),
            ('Amit Patel', 42, '7654321098', 'amit@example.com', 'Surat, Gujarat', user_id, booking_id),
            ('Sneha Desai', 31, '6543210987', 'sneha@example.com', 'Rajkot, Gujarat', user_id, booking_id),
        ]
        
        cursor.executemany('''
            INSERT INTO visitors (full_name, age, phone_number, email, address, user_id, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', test_visitors)
        
        conn.commit()
        flash("Test visitors added successfully", "success")
    else:
        flash("No users or bookings found to associate with test visitors", "error")
    
    conn.close()
    return redirect(url_for('admin_visitors'))

# Incident Reporting Routes
@app.route('/report/incident', methods=['GET', 'POST'])
@login_required
def report_incident():
    if request.method == 'POST':
        try:
            incident_type = request.form.get('type')
            description = request.form.get('description')
            location = request.form.get('location')
            priority = request.form.get('priority', 'medium')
            
            # Handle file upload if exists
            image_path = None
            if 'image' in request.files:
                image = request.files['image']
                if image and image.filename != '':
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"incident_{datetime.now().timestamp()}_{filename}")
                    image.save(image_path)
            
            conn = sqlite3.connect('pilgrim.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO incidents (type, description, location, priority, user_id, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (incident_type, description, location, priority, session['user_id'], image_path))
            
            incident_id = cursor.lastrowid
            
            # Add initial status update
            cursor.execute('''
                INSERT INTO incident_updates (incident_id, status, updated_by, notes)
                VALUES (?, ?, ?, ?)
            ''', (incident_id, 'reported', session['user_id'], 'Incident reported'))
            
            conn.commit()
            conn.close()
            
            flash('Incident reported successfully!', 'success')
            return redirect(url_for('view_incident', incident_id=incident_id))
            
        except Exception as e:
            flash(f'Error reporting incident: {str(e)}', 'error')
            return redirect(url_for('report_incident'))
    
    return render_template('report_incident.html')

@app.route('/incident/<int:incident_id>')
@login_required
def view_incident(incident_id):
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT i.*, u.username as reporter_name 
        FROM incidents i 
        JOIN users u ON i.user_id = u.id 
        WHERE i.id = ?
    ''', (incident_id,))
    incident = cursor.fetchone()
    
    cursor.execute('''
        SELECT u.*, iu.status, iu.notes, iu.timestamp 
        FROM incident_updates iu 
        JOIN users u ON iu.updated_by = u.id 
        WHERE iu.incident_id = ? 
        ORDER BY iu.timestamp DESC
    ''', (incident_id,))
    updates = cursor.fetchall()
    
    # Get available volunteers for assignment
    cursor.execute('''
        SELECT v.user_id, u.username, v.skills, v.location 
        FROM volunteers v 
        JOIN users u ON v.user_id = u.id 
        WHERE v.is_available = 1
    ''')
    volunteers = cursor.fetchall()
    
    conn.close()
    
    if not incident:
        flash('Incident not found', 'error')
        return redirect(url_for('user_dashboard'))
    
    return render_template('view_incident.html', 
                         incident=incident, 
                         updates=updates, 
                         volunteers=volunteers)

@app.route('/incident/update', methods=['POST'])
@login_required
def update_incident():
    incident_id = request.form.get('incident_id')
    status = request.form.get('status')
    notes = request.form.get('notes')
    assigned_to = request.form.get('assigned_to')
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Update incident status
    cursor.execute('UPDATE incidents SET status = ? WHERE id = ?', (status, incident_id))
    
    # Add status update
    cursor.execute('''
        INSERT INTO incident_updates (incident_id, status, updated_by, notes)
        VALUES (?, ?, ?, ?)
    ''', (incident_id, status, session['user_id'], notes))
    
    # Assign to volunteer if provided
    if assigned_to and assigned_to != '0':
        cursor.execute('UPDATE incidents SET assigned_to = ? WHERE id = ?', (assigned_to, incident_id))
    
    conn.commit()
    conn.close()
    
    flash('Incident updated successfully', 'success')
    return redirect(url_for('view_incident', incident_id=incident_id))

@app.route('/my/incidents')
@login_required
def my_incidents():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT i.*, u.username as reporter_name, 
               vu.username as assigned_name 
        FROM incidents i 
        JOIN users u ON i.user_id = u.id 
        LEFT JOIN users vu ON i.assigned_to = vu.id 
        WHERE i.user_id = ? 
        ORDER BY i.timestamp DESC
    ''', (session['user_id'],))
    incidents = cursor.fetchall()
    
    conn.close()
    
    return render_template('my_incidents.html', incidents=incidents)

# Admin incident management
@app.route('/admin/incidents')
@admin_required
def admin_incidents():
    status_filter = request.args.get('status', 'all')
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    if status_filter == 'all':
        cursor.execute('''
            SELECT i.*, u.username as reporter_name, 
                   vu.username as assigned_name 
            FROM incidents i 
            JOIN users u ON i.user_id = u.id 
            LEFT JOIN users vu ON i.assigned_to = vu.id 
            ORDER BY i.timestamp DESC
        ''')
    else:
        cursor.execute('''
            SELECT i.*, u.username as reporter_name, 
                   vu.username as assigned_name 
            FROM incidents i 
            JOIN users u ON i.user_id = u.id 
            LEFT JOIN users vu ON i.assigned_to = vu.id 
            WHERE i.status = ?
            ORDER BY i.timestamp DESC
        ''', (status_filter,))
    
    incidents = cursor.fetchall()
    
    # Get statistics
    cursor.execute('''
        SELECT status, COUNT(*) as count 
        FROM incidents 
        GROUP BY status
    ''')
    stats = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_incidents.html', 
                         incidents=incidents, 
                         stats=stats, 
                         status_filter=status_filter)

# Volunteer registration
@app.route('/volunteer/register', methods=['GET', 'POST'])
@login_required
def volunteer_register():
    if request.method == 'POST':
        skills = request.form.get('skills')
        location = request.form.get('location')
        
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO volunteers (user_id, skills, location)
                VALUES (?, ?, ?)
            ''', (session['user_id'], skills, location))
            
            conn.commit()
            flash('Volunteer registration successful!', 'success')
            return redirect(url_for('user_dashboard'))
            
        except sqlite3.IntegrityError:
            flash('You are already registered as a volunteer', 'info')
            return redirect(url_for('user_dashboard'))
        finally:
            conn.close()
    
    return render_template('volunteer_register.html')

# Volunteer dashboard
@app.route('/volunteer/dashboard')
@login_required
def volunteer_dashboard():
    # Check if user is a volunteer
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM volunteers WHERE user_id = ?', (session['user_id'],))
    volunteer = cursor.fetchone()
    
    if not volunteer:
        flash('You are not registered as a volunteer', 'error')
        return redirect(url_for('user_dashboard'))
    
    # Get assigned incidents
    cursor.execute('''
        SELECT i.*, u.username as reporter_name 
        FROM incidents i 
        JOIN users u ON i.user_id = u.id 
        WHERE i.assigned_to = ? 
        ORDER BY i.timestamp DESC
    ''', (session['user_id'],))
    assigned_incidents = cursor.fetchall()
    
    # Get available incidents (not assigned)
    cursor.execute('''
        SELECT i.*, u.username as reporter_name 
        FROM incidents i 
        JOIN users u ON i.user_id = u.id 
        WHERE i.assigned_to IS NULL AND i.status = 'reported'
        ORDER BY i.priority DESC, i.timestamp ASC
    ''')
    available_incidents = cursor.fetchall()
    
    conn.close()
    
    return render_template('volunteer_dashboard.html', 
                         assigned_incidents=assigned_incidents,
                         available_incidents=available_incidents)

# API endpoint for mobile app
@app.route('/api/incidents', methods=['GET', 'POST'])
def api_incidents():
    if request.method == 'GET':
        # Get incidents based on filters
        status = request.args.get('status', 'reported')
        limit = request.args.get('limit', 50)
        
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.*, u.username as reporter_name 
            FROM incidents i 
            JOIN users u ON i.user_id = u.id 
            WHERE i.status = ?
            ORDER BY i.timestamp DESC
            LIMIT ?
        ''', (status, limit))
        
        incidents = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        result = []
        for incident in incidents:
            result.append({
                'id': incident[0],
                'type': incident[1],
                'description': incident[2],
                'location': incident[3],
                'status': incident[4],
                'priority': incident[5],
                'timestamp': incident[6],
                'reporter_name': incident[10]
            })
        
        return jsonify(result)
    
    elif request.method == 'POST':
        # Report new incident via API
        try:
            data = request.get_json()
            
            conn = sqlite3.connect('pilgrim.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO incidents (type, description, location, priority, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['type'], data['description'], data.get('location'), 
                 data.get('priority', 'medium'), data.get('user_id', 1)))
            
            incident_id = cursor.lastrowid
            
            # Add initial status update
            cursor.execute('''
                INSERT INTO incident_updates (incident_id, status, updated_by, notes)
                VALUES (?, ?, ?, ?)
            ''', (incident_id, 'reported', data.get('user_id', 1), 'Incident reported via API'))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'incident_id': incident_id})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

# ---------- New route: store visitor info linked to user ----------
# @app.route("/submit", methods=["POST"])
# @login_required
# def submit():
#     full_name = request.form["full_name"]
#     age = request.form["age"]
#     phone_number = request.form["phone_number"]
#     email = request.form["email"]
#     address = request.form["address"]

#     conn = sqlite3.connect("pilgrim.db")  # use main database
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO visitors (full_name, age, phone_number, email, address)
#         VALUES (?, ?, ?, ?, ?)
#     """, (full_name, age, phone_number, email, address))
#     conn.commit()
#     conn.close()

#     flash("✅ Visitor information submitted successfully!", "success")
#     return redirect(url_for("user_dashboard"))

@app.route('/download/qr/<int:booking_id>')
@login_required
def download_qr_ticket(booking_id):
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.booking_id, b.persons, b.status, t.temple_name, t.slot_date, t.slot_time, t.duration 
        FROM bookings b
        JOIN time_slots t ON b.slot_id = t.id
        WHERE b.booking_id = ? AND b.user_id = ?
    ''', (booking_id, session['user_id']))
    booking_details = cursor.fetchone()
    conn.close()

    if not booking_details:
        flash("Booking not found or you don't have access.", "error")
        return redirect(url_for('user_dashboard'))

    booking_id_str, persons, status, temple_name, slot_date, slot_time, duration = booking_details
    qr_data = f"Booking ID: {booking_id_str}\nTemple: {temple_name}\nDate: {slot_date}\nTime: {slot_time}\nPersons: {persons}"

    # Generate QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Create the final ticket image
    base_img = Image.new('RGB', (600, 800), 'white')
    draw = ImageDraw.Draw(base_img)

    # Load a font (ensure 'arial.ttf' exists or provide a valid path)
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_medium = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Paste QR code onto the ticket image
    qr_pos = (200, 100)
    base_img.paste(qr_img, qr_pos)

    # Add text to the ticket
    text_color = "black"
    draw.text((20, 20), f"Pilgrim Booking Confirmation 🎟️", fill=text_color, font=font_large)
    draw.text((20, 450), f"Temple: {temple_name}", fill=text_color, font=font_medium)
    draw.text((20, 490), f"Booking ID: {booking_id_str}", fill=text_color, font=font_small)
    draw.text((20, 520), f"Date: {slot_date}", fill=text_color, font=font_small)
    draw.text((20, 550), f"Time Slot: {slot_time} - Duration: {duration} hours", fill=text_color, font=font_small)
    draw.text((20, 580), f"Persons: {persons}", fill=text_color, font=font_small)
    draw.text((20, 610), f"Status: {status.upper()}", fill=text_color, font=font_small)

    # Save the image to a BytesIO object
    img_byte_arr = BytesIO()
    base_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return send_file(img_byte_arr, as_attachment=True, download_name=f'Pilgrim_Ticket_{booking_id_str}.png', mimetype='image/png')
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


if __name__ == '__main__':
    app.run(debug=True)