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
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # -------------------------
    # Admins table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # -------------------------
    # Time slots table
    # -------------------------
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

    # -------------------------
    # Bookings table - FIXED SCHEMA
    # -------------------------
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
            temple_name TEXT NOT NULL,  -- Changed from 'temple' to 'temple_name'
            slot TEXT NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (slot_id) REFERENCES time_slots (id)
        )
    ''')

    # -------------------------
    # Medical emergencies table
    # -------------------------
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
    # Accommodation bookings table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accommodation_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            guests INTEGER NOT NULL,
            special_requests TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # -------------------------
    # Transportation requests table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transport_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            journey_type TEXT NOT NULL,
            pickup_location TEXT NOT NULL,
            dropoff_location TEXT NOT NULL,
            passengers INTEGER NOT NULL,
            datetime TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # -------------------------
    # Historical data table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            temple_name TEXT NOT NULL,
            estimated_footfall INTEGER NOT NULL
        )
    ''')

    # -------------------------
    # Notifications table
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    # Insert demo admin if not exists
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM admins WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash("admin123")
        cursor.execute('''
            INSERT INTO admins (username, password_hash)
            VALUES (?, ?)
        ''', ('admin', password_hash))
    # Visitors table (for storing visitor details from the form)
    # -------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            booking_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    ''')
    # -------------------------
    # Insert demo user if not exists
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('demo_user',))
    if cursor.fetchone()[0] == 0:
        password_hash = generate_password_hash("demo123")
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('demo_user', 'demo@example.com', password_hash))
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
    # Insert sample time slots if not exists
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM time_slots')
    if cursor.fetchone()[0] == 0:
        today = datetime.now().date()
        temples = ['Somnath Temple', 'Dwarka Temple', 'Ambaji Temple', 'Pavagadh Temple']
        times = ['06:00 - 07:30', '07:30 - 09:00', '09:00 - 10:30', '10:30 - 12:00',
                '12:00 - 13:30', '13:30 - 15:00', '15:00 - 16:30', '16:30 - 18:00']
        
        for temple in temples:
            for i in range(7):  # Next 7 days
                for time_slot in times:
                    slot_date = today + timedelta(days=i)
                    total_slots = random.randint(50, 200)
                    cursor.execute('''
                        INSERT INTO time_slots (temple_name, slot_date, slot_time, total_slots, available_slots)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (temple, slot_date.isoformat(), time_slot, total_slots, total_slots))

    # -------------------------
    # Insert sample historical data if not exists
    # -------------------------
    cursor.execute('SELECT COUNT(*) FROM historical_data')
    if cursor.fetchone()[0] == 0:
        today = datetime.now().date()
        temples = ['Somnath Temple', 'Dwarka Temple', 'Ambaji Temple', 'Pavagadh Temple']
        
        for i in range(30):  # Last 30 days
            date = today - timedelta(days=i)
            for temple in temples:
                # Generate realistic footfall data (higher on weekends)
                day_of_week = date.weekday()
                base_footfall = 500 if day_of_week < 5 else 1500  # Weekdays vs weekends
                footfall = base_footfall + random.randint(-200, 200)
                
                cursor.execute('''
                    INSERT INTO historical_data (date, temple_name, estimated_footfall)
                    VALUES (?, ?, ?)
                ''', (date.isoformat(), temple, footfall))

    conn.commit()
    conn.close()
    print("✅ Database initialized with all tables and demo data")

# Function to check and fix existing database schema
def migrate_existing_db():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Check if bookings table has the old 'temple' column
    cursor.execute("PRAGMA table_info(bookings)")
    booking_columns = [col[1] for col in cursor.fetchall()]
    
    if 'temple' in booking_columns and 'temple_name' not in booking_columns:
        print("🔄 Migrating database schema...")
        # Rename temple to temple_name
        cursor.execute('ALTER TABLE bookings RENAME COLUMN temple TO temple_name')
        print("✅ Renamed 'temple' column to 'temple_name' in bookings table")
    
    # Add any other missing columns to bookings table
    required_columns = ['persons', 'valid_until', 'name']
    for column in required_columns:
        if column not in booking_columns:
            if column == 'persons':
                cursor.execute('ALTER TABLE bookings ADD COLUMN persons INTEGER DEFAULT 1')
            elif column == 'valid_until':
                cursor.execute('ALTER TABLE bookings ADD COLUMN valid_until TIMESTAMP')
            elif column == 'name':
                cursor.execute('ALTER TABLE bookings ADD COLUMN name TEXT')
            print(f"✅ Added missing column '{column}' to bookings table")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    migrate_existing_db()