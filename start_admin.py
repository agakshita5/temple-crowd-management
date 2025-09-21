#!/usr/bin/env python3
"""
Startup script for the admin dashboard
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'joblib', 'pandas', 'numpy', 'scikit-learn', 'xgboost']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed")
    return True

def start_admin_server():
    """Start the admin server"""
    if not check_dependencies():
        return False
    
    print("🚀 Starting Admin Dashboard Server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🔐 Login credentials: admin / admin123")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Change to admin directory and start the server
        os.chdir('admin')
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Admin server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_admin_server()