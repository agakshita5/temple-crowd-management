# database.py
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()

    # -------------------------
    # Users table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            created_at TEXT
        )
    ''')

    # Ensure missing columns exist in users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    if "password_hash" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "created_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")

    # -------------------------
    # Admins table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            created_at TEXT
        )
    ''')

    # Ensure missing columns exist in admins table
    cursor.execute("PRAGMA table_info(admins)")
    admin_columns = [col[1] for col in cursor.fetchall()]
    if "password_hash" not in admin_columns:
        cursor.execute("ALTER TABLE admins ADD COLUMN password_hash TEXT")
    if "created_at" not in admin_columns:
        cursor.execute("ALTER TABLE admins ADD COLUMN created_at TEXT")

    # -------------------------
    # Time slots table
    # -------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS time_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temple_name TEXT NOT NULL,
        slot_date DATE NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        total_slots INTEGER NOT NULL,
        available_slots INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        UNIQUE(temple_name, slot_date, start_time, end_time)
        )
    ''')

    #bookings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        slot_id INTEGER NOT NULL,
        persons INTEGER NOT NULL,
        booking_id TEXT UNIQUE NOT NULL,
        qr_code TEXT,
        booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'confirmed',
        valid_until TIMESTAMP,
        temple_name TEXT,
        slot_time TEXT,
        name TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (slot_id) REFERENCES time_slots (id)
        )
    ''')

    # -------------------------
    # Visitors table (NEW - with proper foreign keys)
    # -------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        age INTEGER,
        phone_number TEXT,
        email TEXT,
        address TEXT,
        user_id INTEGER NOT NULL,
        booking_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    ''')

    # -------------------------
    # Historical data table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            temple_name TEXT,
            estimated_footfall INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT,
            status TEXT DEFAULT 'reported',
            priority TEXT DEFAULT 'medium',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            assigned_to INTEGER,
            image_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id)
        )
    ''')
    
    # Create incident_updates table for tracking status changes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incident_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER,
            status TEXT,
            notes TEXT,
            updated_by INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (incident_id) REFERENCES incidents (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
    ''')
    
    # Create volunteers table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            is_available BOOLEAN DEFAULT TRUE,
            skills TEXT,
            location TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
     # -------------------------
    # Donations table
    # -------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        donation_type TEXT NOT NULL,
        message TEXT,
        payment_method TEXT DEFAULT 'stripe',  -- 'stripe' or 'upi'
        payment_status TEXT DEFAULT 'pending',
        stripe_payment_id TEXT,
        upi_transaction_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')


    # -------------------------
    # Notifications table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT,
            subject TEXT,
            body TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')

    # -------------------------
    # Insert demo admin if not exists
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM admins WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash("admin123")
        cursor.execute('''
            INSERT INTO admins (username, password_hash, created_at)
            VALUES (?, ?, ?)
        ''', ('admin', password_hash, datetime.now().isoformat()))

    # -------------------------
    # Insert demo user if not exists
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('demo_user',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash("demo123")
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        ''', ('demo_user', 'demo@example.com', password_hash, datetime.now().isoformat()))

    # -------------------------
    # Insert sample time slots
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM time_slots')
    if cursor.fetchone()[0] == 0:
        time_slots = [
            "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
            "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00",
            "16:00-17:00", "17:00-18:00"
        ]
        temples = ["Somnath", "Dwarka", "Ambaji", "Pavagadh"]

        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).date()
            for temple in temples:
                for slot in time_slots:
                    total_slots = random.randint(50, 200)
                    cursor.execute('''
                        INSERT INTO time_slots (slot_date, slot_time, temple_name, total_slots, available_slots)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (date.isoformat(), slot, temple, total_slots, total_slots))

    conn.commit()
    conn.close()
    print("✅ Database initialized with tables and demo data")

def insert_visitor(full_name, age, phone_number, email, address, user_id, booking_id):
    """Insert a new visitor into the visitors table with proper foreign keys"""
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO visitors (full_name, age, phone_number, email, address, user_id, booking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (full_name, age, phone_number, email, address, user_id, booking_id))
    conn.commit()
    conn.close()
    return True

def fetch_visitors_by_user(user_id, limit=50):
    """Fetch visitor records for a specific user"""
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.id, v.full_name, v.age, v.phone_number, v.email, v.address, 
               b.booking_id, t.temple_name, t.slot_date, t.slot_time
        FROM visitors v
        JOIN bookings b ON v.booking_id = b.id
        JOIN time_slots t ON b.slot_id = t.id
        WHERE v.user_id = ?
        ORDER BY v.id DESC LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_all_visitors(limit=50):
    """Fetch all visitor records with booking details"""
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.id, v.full_name, v.age, v.phone_number, v.email, v.address, 
               u.username, b.booking_id, t.temple_name, t.slot_date, t.slot_time
        FROM visitors v
        JOIN users u ON v.user_id = u.id
        JOIN bookings b ON v.booking_id = b.id
        JOIN time_slots t ON b.slot_id = t.id
        ORDER BY v.id DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_visitor(visitor_id):
    """Delete a visitor by ID"""
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM visitors WHERE id = ?', (visitor_id,))
    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    init_db()