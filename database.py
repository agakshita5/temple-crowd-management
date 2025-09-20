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
            slot_date TEXT,
            slot_time TEXT,
            temple_name TEXT,
            total_slots INTEGER,
            available_slots INTEGER
        )
    ''')

    # -------------------------
    # Bookings table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            slot_id INTEGER,
            booking_id INTEGER,
            qr_code TEXT,
            booking_time TEXT,
            status TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (slot_id) REFERENCES time_slots(id)
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


if __name__ == "__main__":
    init_db()