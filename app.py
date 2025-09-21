from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash, check_password_hash
import crowd_prediction
import qrcode
import os
import io
from functools import wraps
import requests
import json
import stripe
app = Flask(__name__)
app.secret_key = 'pilgrim_secret_key'

stripe.api_key = "REMOVEDY3IQW8fY5qAnlngq7SziCL1ypMXcLcbiVu0FOQmkkGseDB6wfosb1EoAriqioM8ykZYWmxD2hMYrjAvK4jyxT00nARclhw4"
STRIPE_PUBLISHABLE_KEY = "REMOVED3IQW8fY5qAnl73PdcNdfIovzFy8mzDHMpWMqSkaiLdq9s2cTQT7JEHfrhUHYL5C16SAXsAJFn7039pPYikvV00aW0yg2Mi"


UPI_ID = "7014080430@axl"
PAYEE_NAME = "Sonam Yadav"
# Initialize DB - FIXED SCHEMA
def init_db():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admins table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Create time_slots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temple_name TEXT NOT NULL,
            slot_date DATE NOT NULL,
            slot_time TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            UNIQUE(temple_name, slot_date, slot_time)
        )
    ''')
    
    # Create bookings table - FIXED: Using temple_name consistently
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            persons INTEGER NOT NULL,
            booking_id TEXT UNIQUE NOT NULL,
            qr_code TEXT,
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            valid_until TIMESTAMP,
            temple_name TEXT,  -- Using temple_name consistently
            slot TEXT,
            name TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (slot_id) REFERENCES time_slots (id)
        )
    ''')
    
    # Create notifications_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create historical_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            temple_name TEXT NOT NULL,
            estimated_footfall INTEGER NOT NULL
        )
    ''')
    # Create donations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            donation_type TEXT NOT NULL,
            message TEXT,
            payment_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create medical_emergencies table with all required columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            emergency_type TEXT NOT NULL,
            location TEXT NOT NULL,
            details TEXT,
            contact_number TEXT NOT NULL,
            affected_persons INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute('SELECT COUNT(*) FROM admins')
    if cursor.fetchone()[0] == 0:
        admin_hash = generate_password_hash('admin123')
        cursor.execute('INSERT INTO admins (username, password_hash) VALUES (?, ?)', 
                      ('admin', admin_hash))
    
    # Insert sample time slots if not exists
    cursor.execute('SELECT COUNT(*) FROM time_slots')
    if cursor.fetchone()[0] == 0:
        today = datetime.now().date()
        temples = ['Somnath Temple', 'Dwarka Temple', 'Ambaji Temple']
        times = ['06:00 - 07:30', '07:30 - 09:00', '09:00 - 10:30', '10:30 - 12:00']
        
        for temple in temples:
            for i in range(7):  # Next 7 days
                for time_slot in times:
                    slot_date = today + timedelta(days=i)
                    cursor.execute('''
                        INSERT INTO time_slots (temple_name, slot_date, slot_time, total_slots, available_slots)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (temple, slot_date, time_slot, 100, 100))
    
    conn.commit()
    conn.close()

# Function to migrate existing database
def migrate_database():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Check if medical_emergencies table exists and has the required columns
    cursor.execute("PRAGMA table_info(medical_emergencies)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add missing columns to medical_emergencies table
    if 'affected_persons' not in columns:
        cursor.execute("ALTER TABLE medical_emergencies ADD COLUMN affected_persons INTEGER DEFAULT 1")
        print("✅ Added affected_persons column to medical_emergencies table")
    
    if 'admin_notes' not in columns:
        cursor.execute("ALTER TABLE medical_emergencies ADD COLUMN admin_notes TEXT")
        print("✅ Added admin_notes column to medical_emergencies table")
    
    # Check if bookings table has the correct columns
    cursor.execute("PRAGMA table_info(bookings)")
    booking_columns = [col[1] for col in cursor.fetchall()]
    
    # Rename temple to temple_name if needed
    if 'temple' in booking_columns and 'temple_name' not in booking_columns:
        cursor.execute('ALTER TABLE bookings RENAME COLUMN temple TO temple_name')
        print("✅ Renamed temple column to temple_name in bookings table")
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()
# Migrate existing database
migrate_database()

# Enable SQLite to auto-convert date/time columns
sqlite3.register_adapter(datetime, lambda val: val.isoformat())
sqlite3.register_converter("timestamp", lambda val: datetime.fromisoformat(val.decode("utf-8")))

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": False, "message": "Login required"}), 401
            flash("Please login first", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
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

        conn = sqlite3.connect(
            'pilgrim.db',
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        cursor = conn.cursor()

        try:
            password_hash = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, datetime.now().isoformat()))
            conn.commit()
            flash("✅ Registration successful! Please login.", "success")
            return redirect(url_for('index'))
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

    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, password_hash, email 
        FROM users 
        WHERE username = ? OR email = ?
    ''', (identifier, identifier))
    
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
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
    temple_name = "Somnath Temple"
    
    # Get crowd prediction for today
    prediction = crowd_prediction.predict_crowd(today, temple_name)
    
    # Get available slots
    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
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
                           temple_name=temple_name)



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

# # ----------------- DONATION ROUTES -----------------
# @app.route('/donate', methods=['GET', 'POST'])
# @login_required
# def donate():
#     if request.method == 'POST':
#         amount = request.form.get('amount')
#         donation_type = request.form.get('donation_type')
#         message = request.form.get('message', '')

#         if not amount or not donation_type:
#             flash("Please fill all required fields", "error")
#             return redirect(url_for('donate'))

#         try:
#             amount = float(amount)
#             if amount <= 0:
#                 flash("Please enter a valid donation amount", "error")
#                 return redirect(url_for('donate'))
#         except ValueError:
#             flash("Please enter a valid donation amount", "error")
#             return redirect(url_for('donate'))

#         conn = sqlite3.connect('pilgrim.db')
#         cursor = conn.cursor()
#         cursor.execute('''
#             INSERT INTO donations (user_id, amount, donation_type, message, payment_status)
#             VALUES (?, ?, ?, ?, ?)
#         ''', (session['user_id'], amount, donation_type, message, 'pending'))
#         donation_id = cursor.lastrowid
#         conn.commit()
#         conn.close()

#         return redirect(url_for('donate_upi_qr', donation_id=donation_id))

#     return render_template('donate.html')

# @app.route('/donate/upi_qr/<int:donation_id>')
# @login_required
# def donate_upi_qr(donation_id):
#     # Fetch donation info
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT amount, donation_type FROM donations WHERE id = ?', (donation_id,))
#     donation = cursor.fetchone()
#     conn.close()

#     if not donation:
#         flash("Donation record not found", "error")
#         return redirect(url_for('donate'))

#     amount, donation_type = donation

#     # UPI details
    
#     transaction_note = donation_type

#     # Generate UPI link
#     upi_link = f"upi://pay?pa={upi_id}&pn={payee_name}&tn={transaction_note}&am={amount}&cu=INR"

#     # Generate QR code
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4
#     )
#     qr.add_data(upi_link)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color="black", back_color="white")

#     img_buffer = io.BytesIO()
#     img.save(img_buffer, format='PNG')
#     img_buffer.seek(0)

#     return send_file(
#         img_buffer,
#         mimetype='image/png',
#         as_attachment=False,
#         download_name=f'donation_{donation_id}_upi.png'
#     )

# @app.route('/donate/confirm/<int:donation_id>')
# @login_required
# def donate_confirm(donation_id):
#     # Mark donation as paid manually (after scanning UPI)
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('UPDATE donations SET payment_status = ? WHERE id = ?', ('paid', donation_id))
#     conn.commit()
#     conn.close()

#     flash("Thank you for your donation! Payment confirmed successfully.", "success")
#     return redirect(url_for('user_dashboard'))

@app.route('/applications')
@login_required
def applications():
    # Get user bookings
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Check if temple_name column exists, otherwise use temple
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'temple_name' in columns:
        cursor.execute('''
            SELECT b.booking_id, b.temple_name, b.slot, b.booking_time, b.status, b.persons
            FROM bookings b
            WHERE b.user_id = ?
            ORDER BY b.booking_time DESC
        ''', (session['user_id'],))
    else:
        cursor.execute('''
            SELECT b.booking_id, b.temple, b.slot, b.booking_time, b.status, b.persons
            FROM bookings b
            WHERE b.user_id = ?
            ORDER BY b.booking_time DESC
        ''', (session['user_id'],))
    
    bookings = cursor.fetchall()
    conn.close()

    # Define other applications - UPDATED WITH DONATION LINK
    other_apps = [
        {"name": "Book Temple Slot", "description": "Reserve your temple visit slot", "link": "/user/dashboard"},
        {"name": "Medical Emergency", "description": "Request immediate medical assistance", "link": "#"},
        {"name": "Crowd Status", "description": "Check current temple crowd levels", "link": "/crowd-status"},
        {"name": "Donate / Offer", "description": "Make donations or offerings online", "link": "/donate"},
        {"name": "Accommodation", "description": "Book nearby accommodation", "link": "/accommodation"},
        {"name": "Transportation", "description": "Arrange transportation", "link": "/transport"}
    ]
    
    return render_template('applications.html', bookings=bookings, other_apps=other_apps)

# Add Medical Emergency Route
@app.route('/medical-emergency', methods=['POST'])
@login_required
def medical_emergency():
    if request.method == 'POST':
        emergency_type = request.form.get('emergency_type')
        location = request.form.get('location')
        details = request.form.get('details')
        contact = request.form.get('contact')
        affected_persons = request.form.get('affected_persons', 1)
        
        conn = sqlite3.connect('pilgrim.db')
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute('SELECT username, email FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        # Check if affected_persons column exists
        cursor.execute("PRAGMA table_info(medical_emergencies)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'affected_persons' in columns:
            cursor.execute('''
                INSERT INTO medical_emergencies (user_id, emergency_type, location, details, contact_number, affected_persons)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], emergency_type, location, details, contact, affected_persons))
        else:
            cursor.execute('''
                INSERT INTO medical_emergencies (user_id, emergency_type, location, details, contact_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], emergency_type, location, details, contact))
        
        emergency_id = cursor.lastrowid
        
        # Also log this as a notification
        cursor.execute('''
            INSERT INTO notifications_log (recipient, subject, status)
            VALUES (?, ?, ?)
        ''', ('admin', f'Medical Emergency Alert - {emergency_type}', 'urgent'))
        
        conn.commit()
        conn.close()
        
        flash('Emergency assistance requested! Help has been alerted and will arrive soon.', 'success')
        return redirect(url_for('applications'))

# Add Admin Medical Emergencies Route
@app.route('/admin/medical-emergencies')
@admin_required
def admin_medical_emergencies():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT me.id, u.username, me.emergency_type, me.location, me.details, 
               me.contact_number, me.affected_persons, me.status, me.created_at
        FROM medical_emergencies me
        JOIN users u ON me.user_id = u.id
        ORDER BY me.created_at DESC
    ''')
    
    emergencies = cursor.fetchall()
    conn.close()
    
    return render_template('admin_medical_emergencies.html', emergencies=emergencies)

# Add Update Medical Emergency Route
@app.route('/admin/medical-emergency/<int:emergency_id>/update', methods=['POST'])
@admin_required
def update_medical_emergency(emergency_id):
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE medical_emergencies 
        SET status = ?, admin_notes = ?, resolved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, admin_notes, emergency_id))
    
    conn.commit()
    conn.close()
    
    flash('Emergency status updated successfully', 'success')
    return redirect(url_for('admin_medical_emergencies'))

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = f"user{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('user_dashboard'))
    return render_template('upload.html')

@app.route('/book/slot', methods=['POST'])
@login_required
def book_slot():
    slot_id = request.form.get('slot_id')
    persons = int(request.form.get('persons', 1))

    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT slot_date, slot_time, temple_name, available_slots FROM time_slots WHERE id = ?', (slot_id,))
    slot = cursor.fetchone()

    if not slot or slot['available_slots'] < persons:
        conn.close()
        return jsonify({'success': False, 'message': 'Slot no longer available'})

    # Create booking
    booking_id = random.randint(100000, 999999)
    booking_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
    valid_until = (datetime.now() + timedelta(hours=1, minutes=30)).strftime("%d %b %Y, %I:%M %p")

    cursor.execute('SELECT username, email FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()

    # FIXED: Using 'temple_name' instead of 'temple' to match database schema
    cursor.execute('''
        INSERT INTO bookings (user_id, slot_id, persons, booking_id, qr_code, booking_time, status, valid_until, temple_name, slot, name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session['user_id'], slot_id, persons, booking_id,
        f'QR_{booking_id}', booking_time, 'confirmed',
        valid_until, slot['temple_name'], slot['slot_time'], user['username']
    ))

    # Update available slots
    cursor.execute('UPDATE time_slots SET available_slots = available_slots - ? WHERE id = ?', (persons, slot_id))

    conn.commit()
    conn.close()

    # Generate QR with details
    qr_text = (
        f"Booking ID: {booking_id}\n"
        f"Name: {user['username']}\n"
        f"Email: {user['email']}\n"
        f"Temple: {slot['temple_name']}\n"
        f"Date: {slot['slot_date']} at {slot['slot_time']}\n"
        f"Persons: {persons}\n"
        f"Booking Time: {booking_time}\n"
        f"Valid Until: {valid_until}"
    )

    qr_filename = f"QR_{booking_id}.png"
    qr_folder = os.path.join("static", "qrcodes")
    os.makedirs(qr_folder, exist_ok=True)
    qr_path = os.path.join(qr_folder, qr_filename)

    qr = qrcode.make(qr_text)
    qr.save(qr_path)

    return jsonify({
        'success': True,
        'message': 'Booking confirmed successfully',
        'booking_id': booking_id,
        'qr_code_url': url_for('static', filename=f"qrcodes/{qr_filename}")
    })

@app.route('/download_qr/<booking_id>')
@login_required
def download_qr(booking_id):
    # Get booking details
    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    cursor = conn.cursor()
    
    # FIXED: Changed 'b.temple' to 'b.temple_name' to match database schema
    cursor.execute('''
        SELECT b.booking_id, b.name, b.temple_name, b.slot, b.valid_until, b.booking_time, b.persons, u.email
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.booking_id = ?
    ''', (booking_id,))
    
    booking = cursor.fetchone()
    conn.close()
    
    if not booking:
        flash("Booking not found", "error")
        return redirect(url_for('user_dashboard'))
    
    # Create QR code text
    qr_text = (
        f"Temple: {booking[2]}\n"
        f"Slot: {booking[3]}\n"
        f"Booking Time: {booking[5]}\n"
        f"Valid Until: {booking[4]}\n"
        f"Persons: {booking[6]}\n"
        f"Name: {booking[1]}\n"
        f"Email: {booking[7]}\n"
        f"Booking ID: {booking[0]}"
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image to bytes buffer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return send_file(
        img_buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'Pilgrim_QR_{booking_id}.png'
    )

@app.route('/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    data = request.json
    payment_id = data.get('payment_id')
    order_id = data.get('order_id')
    signature = data.get('signature')
    booking_id = data.get('booking_id')
    
    # In a real implementation, you would verify the payment signature with Razorpay
    # For demo purposes, we'll assume payment is successful
    
    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
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

# # Donation Routes
# @app.route('/donate', methods=['GET'])
# @login_required
# def donate():
#     return render_template('donate.html', key_id=RAZORPAY_KEY_ID)

# @app.route('/create_order', methods=['POST'])
# @login_required
# def create_order():
#     amount = int(request.form.get('amount')) * 100  # amount in paise
#     donation_type = request.form.get('donation_type')
#     message = request.form.get('message', '')

#     order_data = {
#         "amount": amount,
#         "currency": "INR",
#         "payment_capture": "1"
#     }
#     razorpay_order = client.order.create(data=order_data)
#     order_id = razorpay_order['id']

#     # Save donation in DB as pending
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO donations (user_id, amount, donation_type, message, payment_status)
#         VALUES (?, ?, ?, ?, ?)
#     ''', (session['user_id'], amount/100, donation_type, message, 'pending'))
#     donation_id = cursor.lastrowid
#     conn.commit()
#     conn.close()

#     return render_template('pay.html',
#                            donation_id=donation_id,
#                            order_id=order_id,
#                            amount=amount,
#                            key_id=RAZORPAY_KEY_ID)

# @app.route('/payment_success', methods=['POST'])
# @login_required
# def payment_success():
#     payment_id = request.form.get('razorpay_payment_id')
#     order_id = request.form.get('razorpay_order_id')
#     signature = request.form.get('razorpay_signature')
#     donation_id = request.form.get('donation_id')

#     params_dict = {
#         'razorpay_order_id': order_id,
#         'razorpay_payment_id': payment_id,
#         'razorpay_signature': signature
#     }

#     try:
#         # Verify signature with Razorpay
#         client.utility.verify_payment_signature(params_dict)
#         conn = sqlite3.connect('pilgrim.db')
#         cursor = conn.cursor()
#         cursor.execute('UPDATE donations SET payment_status = ? WHERE id = ?', ('completed', donation_id))
#         conn.commit()
#         conn.close()
#         return jsonify({"success": True})
#     except Exception as e:
#         conn = sqlite3.connect('pilgrim.db')
#         cursor = conn.cursor()
#         cursor.execute('UPDATE donations SET payment_status = ? WHERE id = ?', ('failed', donation_id))
#         conn.commit()
#         conn.close()
#         print("Payment verification error:", e)
#         return jsonify({"success": False})



# @app.route('/donate/process', methods=['POST'])
# @login_required
# def process_donation():
#     amount = request.form.get('amount')
#     donation_type = request.form.get('donation_type')
#     message = request.form.get('message', '')

#     if not amount or not donation_type:
#         flash("Please fill all required fields", "error")
#         return redirect(url_for('donate'))

#     try:
#         amount = float(amount)
#         if amount <= 0:
#             flash("Please enter a valid donation amount", "error")
#             return redirect(url_for('donate'))
#     except ValueError:
#         flash("Please enter a valid donation amount", "error")
#         return redirect(url_for('donate'))

#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()

#     # Insert donation record with pending payment
#     cursor.execute('''
#         INSERT INTO donations (user_id, amount, donation_type, message, payment_status)
#         VALUES (?, ?, ?, ?, ?)
#     ''', (session['user_id'], amount, donation_type, message, 'pending'))

#     donation_id = cursor.lastrowid

#     # Log notification for admin
#     cursor.execute('''
#         INSERT INTO notifications_log (recipient, subject, status)
#         VALUES (?, ?, ?)
#     ''', ('admin', f'New Donation - ₹{amount} for {donation_type}', 'info'))

#     conn.commit()
#     conn.close()

#     # Simulate payment success (In real app, integrate a gateway like Razorpay/UPI)
#     return redirect(url_for('donation_payment_success', donation_id=donation_id))


# # Route to simulate payment success
# @app.route('/donate/success/<int:donation_id>')
# @login_required
# def donation_payment_success(donation_id):
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()

#     # Update donation as paid
#     cursor.execute('''
#         UPDATE donations
#         SET payment_status = ?
#         WHERE id = ?
#     ''', ('paid', donation_id))
#     conn.commit()
#     conn.close()

#     flash('Thank you for your donation! Payment confirmed successfully.', 'success')
#     return redirect(url_for('applications'))


# Admin view donations
@app.route('/admin/donations')
@admin_required
def admin_donations():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT d.id, u.username, d.amount, d.donation_type, d.message, 
               d.payment_status, d.created_at
        FROM donations d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC
    ''')

    donations = cursor.fetchall()
    conn.close()

    return render_template('admin_donations.html', donations=donations)


# Admin update donation status manually
@app.route('/admin/donation/<int:donation_id>/update', methods=['POST'])
@admin_required
def update_donation(donation_id):
    payment_status = request.form.get('payment_status')

    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE donations 
        SET payment_status = ?
        WHERE id = ?
    ''', (payment_status, donation_id))

    conn.commit()
    conn.close()

    flash('Donation status updated successfully', 'success')
    return redirect(url_for('admin_donations'))

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
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
    # Generate 7-day predictions
    predictions = []
    temple_name = "Somnath Temple"
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        prediction = crowd_prediction.predict_crowd(date, temple_name)
        predictions.append({'date': date.date(), 'prediction': prediction})

    # Get recent bookings
    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
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
@admin_required
def view_notifications():
    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    cursor = conn.cursor()

    cursor.execute("SELECT recipient, subject, status, created_at FROM notifications_log ORDER BY created_at DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template("admin_notifications.html", logs=logs)

@app.route('/visualization')
def visualization():
    conn = sqlite3.connect(
        'pilgrim.db',
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE
    )
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