# import sqlite3
# from datetime import datetime, timedelta
# import random
# from werkzeug.security import generate_password_hash

# def init_db():
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
    
#     # Create users table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY,
#             username TEXT UNIQUE,
#             email TEXT,
#             created_at TEXT
#         )
#     ''')
    
#     # Create time_slots table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS time_slots (
#             id INTEGER PRIMARY KEY,
#             slot_date TEXT,
#             slot_time TEXT,
#             temple_name TEXT,
#             total_slots INTEGER,
#             available_slots INTEGER
#         )
#     ''')
    
#     # Create bookings table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS bookings (
#             id INTEGER PRIMARY KEY,
#             user_id INTEGER,
#             slot_id INTEGER,
#             booking_id INTEGER,
#             qr_code TEXT,
#             booking_time TEXT,
#             FOREIGN KEY (user_id) REFERENCES users (id),
#             FOREIGN KEY (slot_id) REFERENCES time_slots (id)
#         )
#     ''')
    
#     # Create historical_data table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS historical_data (
#             id INTEGER PRIMARY KEY,
#             date TEXT,
#             temple_name TEXT,
#             estimated_footfall INTEGER
#         )
#     ''')
    
#     # ✅ Create admins table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS admins (
#             id INTEGER PRIMARY KEY,
#             username TEXT UNIQUE,
#             password_hash TEXT,
#             created_at TEXT
#         )
#     ''')
    
#     # Insert sample time slots if they don't exist
#     cursor.execute('SELECT COUNT(*) FROM time_slots')
#     count = cursor.fetchone()[0]
    
#     if count == 0:
#         time_slots = [
#             "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
#             "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00",
#             "16:00-17:00", "17:00-18:00"
#         ]
#         temples = ["Somnath", "Dwarka", "Ambaji", "Pavagadh"]
        
#         for i in range(7):
#             date = (datetime.now() + timedelta(days=i)).date()
#             for temple in temples:
#                 for slot in time_slots:
#                     total_slots = random.randint(50, 200)
#                     cursor.execute('''
#                         INSERT INTO time_slots (slot_date, slot_time, temple_name, total_slots, available_slots)
#                         VALUES (?, ?, ?, ?, ?)
#                     ''', (date.isoformat(), slot, temple, total_slots, total_slots))
    
#     # Insert a demo user
#     cursor.execute('SELECT COUNT(*) FROM users')
#     user_count = cursor.fetchone()[0]
#     if user_count == 0:
#         cursor.execute('''
#             INSERT INTO users (username, email, created_at)
#             VALUES (?, ?, ?)
#         ''', ('demo_user', 'demo@example.com', datetime.now().isoformat()))
    
#     # ✅ Insert a default admin if none exists
#     # cursor.execute('SELECT COUNT(*) FROM admins')
#     # admin_count = cursor.fetchone()[0]
#     # if admin_count == 0:
#     #     password_hash = generate_password_hash("admin123")  # default password
#     #     cursor.execute('''
#     #         INSERT INTO admins (username, password_hash, created_at)
#     #         VALUES (?, ?, ?)
#     #     ''', ('admin', password_hash, datetime.now().isoformat()))

#     # Insert demo admin if not exists
#     cursor.execute('SELECT COUNT(*) FROM admins WHERE username = ?', ('admin',))
#     admin_count = cursor.fetchone()[0]

#     if admin_count == 0:
#         from werkzeug.security import generate_password_hash
#         password_hash = generate_password_hash("admin123")
#         cursor.execute('''
#             INSERT INTO admins (username, password_hash, created_at)
#             VALUES (?, ?, ?)
#         ''', ('admin', password_hash, datetime.now().isoformat()))
    
#     conn.commit()
#     conn.close()

# if __name__ == "__main__":
#     init_db()
#     print("✅ Database initialized with tables and demo data")


# import sqlite3
# from datetime import datetime, timedelta
# import random
# from werkzeug.security import generate_password_hash

# def init_db():
#     conn = sqlite3.connect('pilgrim.db')
#     cursor = conn.cursor()
    
#     # Create users table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY,
#             username TEXT UNIQUE,
#             email TEXT,
#             created_at TEXT
#         )
#     ''')
    
#     # Create time_slots table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS time_slots (
#             id INTEGER PRIMARY KEY,
#             slot_date TEXT,
#             slot_time TEXT,
#             temple_name TEXT,
#             total_slots INTEGER,
#             available_slots INTEGER
#         )
#     ''')
    
#     # Create bookings table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS bookings (
#             id INTEGER PRIMARY KEY,
#             user_id INTEGER,
#             slot_id INTEGER,
#             persons INTEGER,
#             booking_id INTEGER,
#             qr_code TEXT,
#             booking_time TEXT,
#             FOREIGN KEY (user_id) REFERENCES users (id),
#             FOREIGN KEY (slot_id) REFERENCES time_slots (id)
#         )
#     ''')
    
#     # Create historical_data table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS historical_data (
#             id INTEGER PRIMARY KEY,
#             date TEXT,
#             temple_name TEXT,
#             estimated_footfall INTEGER
#         )
#     ''')
    
#     # Create admins table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS admins (
#             id INTEGER PRIMARY KEY,
#             username TEXT UNIQUE,
#             password_hash TEXT,
#             created_at TEXT
#         )
#     ''')
    
#     # Insert sample time slots if they don't exist
#     cursor.execute('SELECT COUNT(*) FROM time_slots')
#     count = cursor.fetchone()[0]
    
#     if count == 0:
#         time_slots = [
#             "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
#             "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00",
#             "16:00-17:00", "17:00-18:00"
#         ]
#         temples = ["Somnath", "Dwarka", "Ambaji", "Pavagadh"]
        
#         for i in range(7):
#             date = (datetime.now() + timedelta(days=i)).date()
#             for temple in temples:
#                 for slot in time_slots:
#                     total_slots = random.randint(50, 200)
#                     cursor.execute('''
#                         INSERT INTO time_slots (slot_date, slot_time, temple_name, total_slots, available_slots)
#                         VALUES (?, ?, ?, ?, ?)
#                     ''', (date.isoformat(), slot, temple, total_slots, total_slots))
    
#     # Insert a demo user
#     cursor.execute('SELECT COUNT(*) FROM users')
#     user_count = cursor.fetchone()[0]
#     if user_count == 0:
#         cursor.execute('''
#             INSERT INTO users (username, email, created_at)
#             VALUES (?, ?, ?)
#         ''', ('demo_user', 'demo@example.com', datetime.now().isoformat()))
    
#     # Insert demo admin if not exists
#     cursor.execute('SELECT COUNT(*) FROM admins WHERE username = ?', ('admin',))
#     admin_count = cursor.fetchone()[0]

#     if admin_count == 0:
#         password_hash = generate_password_hash("admin123")
#         cursor.execute('''
#             INSERT INTO admins (username, password_hash, created_at)
#             VALUES (?, ?, ?)
#         ''', ('admin', password_hash, datetime.now().isoformat()))
    
#     conn.commit()
#     conn.close()

# if __name__ == "__main__":
#     init_db()
#     print("✅ Database initialized with tables and demo data")


import sqlite3
from datetime import datetime, timedelta
import random

def init_db():
    conn = sqlite3.connect('pilgrim.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT,
            phone TEXT,
            created_at TEXT
        )
    ''')
    
    # Create time_slots table with slot types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY,
            slot_date TEXT,
            slot_type TEXT,
            slot_time TEXT,
            temple_name TEXT,
            total_slots INTEGER,
            available_slots INTEGER,
            price DECIMAL(10,2)
        )
    ''')
    
    # Create bookings table with payment status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            slot_id INTEGER,
            booking_id TEXT,
            qr_code TEXT,
            booking_time TEXT,
            payment_status TEXT DEFAULT 'pending',
            payment_id TEXT,
            entry_scan_time TEXT,
            exit_scan_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (slot_id) REFERENCES time_slots (id)
        )
    ''')
    
    # Create payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            booking_id INTEGER,
            amount DECIMAL(10,2),
            payment_method TEXT,
            payment_status TEXT,
            transaction_id TEXT,
            payment_time TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings (id)
        )
    ''')
    
    # Insert sample time slots if they don't exist
    cursor.execute('SELECT COUNT(*) FROM time_slots')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Define slot types and times
        slot_types = {
            'Morning': ['06:00-07:30', '07:30-09:00', '09:00-10:30'],
            'Afternoon': ['10:30-12:00', '12:00-13:30', '13:30-15:00'],
            'Evening': ['15:00-16:30', '16:30-18:00', '18:00-19:30']
        }
        
        temples = ["Somnath", "Dwarka", "Ambaji", "Pavagadh"]
        prices = {
            'Morning': 100.00,
            'Afternoon': 150.00,
            'Evening': 200.00
        }
        
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).date()
            
            for temple in temples:
                for slot_type, times in slot_types.items():
                    for slot_time in times:
                        total_slots = random.randint(50, 200)
                        cursor.execute('''
                            INSERT INTO time_slots (slot_date, slot_type, slot_time, temple_name, total_slots, available_slots, price)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (date.isoformat(), slot_type, slot_time, temple, total_slots, total_slots, prices[slot_type]))
    
    # Insert a demo user
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        cursor.execute('''
            INSERT INTO users (username, email, phone, created_at)
            VALUES (?, ?, ?, ?)
        ''', ('demo_user', 'demo@example.com', '+1234567890', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()