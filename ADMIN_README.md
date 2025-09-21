# Temple Crowd Management - Admin Dashboard

## 🎯 Overview

The Admin Dashboard is a comprehensive real-time management system for temple administrators to monitor and manage temple operations, crowd levels, emergencies, and incidents.

## 🚀 Features

### ✅ **Real-Time Dashboard**
- Live statistics for bookings, emergencies, and incidents
- Auto-refresh every 30 seconds
- Current time slot information with crowd prediction
- Real-time data updates without page reload

### 📊 **Crowd Prediction**
- AI-powered crowd level prediction using trained XGBoost model
- Predictions for all time slots throughout the day
- Visual indicators (Low/Medium/High) with color coding
- Historical data integration for accurate predictions

### 🚨 **Emergency Management**
- Real-time emergency alerts and notifications
- Medical emergency tracking and resolution
- Contact information and location details
- Status updates (Pending/Resolved)

### 📋 **Incident Management**
- Incident reporting and tracking system
- Priority-based incident handling
- Investigation workflow
- Status updates and admin notes

### 📅 **Slot Management**
- Today's time slot overview
- Available vs. total slot tracking
- Booking capacity monitoring
- Crowd level predictions per slot

### 👥 **Booking Management**
- Today's booking overview
- User details and contact information
- Booking status tracking
- QR code integration

## 🛠️ Technical Implementation

### **Backend (Flask)**
- **File**: `admin/app.py`
- **Database**: SQLite (`pilgrim.db`)
- **AI Model**: XGBoost for crowd prediction
- **APIs**: RESTful endpoints for real-time data

### **Frontend (HTML/CSS/JavaScript)**
- **File**: `templates/admin_dashboard.html`
- **Framework**: Bootstrap 5
- **Features**: Responsive design, real-time updates
- **Icons**: Font Awesome

### **Database Schema**
- `time_slots`: Temple time slot management
- `bookings`: User booking records
- `medical_emergencies`: Emergency tracking
- `incidents`: Incident management
- `users`: User information
- `historical_data`: Crowd prediction data

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install flask joblib pandas numpy scikit-learn xgboost
```

### 2. **Initialize Database**
```bash
python database.py
```

### 3. **Start Admin Server**
```bash
python start_admin.py
```

### 4. **Access Dashboard**
- **URL**: http://localhost:5000/admin/login
- **Username**: `admin`
- **Password**: `admin123`

## 📱 Dashboard Sections

### **Main Dashboard**
- Statistics cards showing real-time counts
- Current time slot information
- Recent emergencies and incidents
- Live crowd level indicator

### **Slot Management**
- View all time slots for today
- See available vs. total capacity
- Crowd prediction for each slot
- Visual progress bars

### **Emergency Management**
- List of all medical emergencies
- Contact details and locations
- Status tracking and resolution
- Admin action buttons

### **Incident Management**
- All reported incidents
- Investigation workflow
- Priority and status tracking
- Admin notes and updates

### **Booking Management**
- Today's booking overview
- User details and contact info
- Booking status tracking
- Time slot assignments

### **Crowd Prediction**
- AI-powered predictions for all slots
- Visual crowd level indicators
- Capacity utilization charts
- Historical trend analysis

## 🔧 API Endpoints

### **Authentication**
- `POST /admin/login` - Admin login
- `GET /admin/logout` - Admin logout

### **Dashboard Data**
- `GET /admin/api/dashboard-data` - Real-time dashboard statistics
- `GET /admin/api/crowd-prediction` - Crowd predictions for today
- `GET /admin/api/slots/<date>` - Time slots for specific date

### **Emergency Management**
- `GET /admin/api/emergencies` - List all emergencies
- `POST /admin/api/emergencies/update` - Update emergency status

### **Incident Management**
- `GET /admin/api/incidents` - List all incidents
- `POST /admin/api/incidents/update` - Update incident status

## 🎨 UI Features

### **Responsive Design**
- Mobile-friendly interface
- Bootstrap 5 components
- Adaptive layout for all screen sizes

### **Real-Time Updates**
- Auto-refresh every 30 seconds
- Live data indicators
- Smooth animations and transitions

### **Visual Indicators**
- Color-coded crowd levels (Green/Yellow/Red)
- Status badges for emergencies and incidents
- Progress bars for slot capacity
- Live update timestamps

### **Interactive Elements**
- Clickable navigation menu
- Action buttons for status updates
- Modal dialogs for detailed views
- Refresh button for manual updates

## 🔒 Security Features

- Session-based authentication
- Admin-only access to sensitive data
- CSRF protection
- Secure password handling

## 📊 Data Flow

1. **User Bookings** → `pilgrim.db` → **Admin Dashboard**
2. **Emergency Reports** → `medical_emergencies` table → **Real-time Alerts**
3. **Incident Reports** → `incidents` table → **Investigation Workflow**
4. **Historical Data** → **AI Model** → **Crowd Predictions**

## 🚨 Emergency Workflow

1. **Report Received** → Dashboard shows new emergency
2. **Admin Review** → View details and contact information
3. **Action Taken** → Update status (Investigating/Resolved)
4. **Resolution** → Mark as resolved with admin notes

## 📈 Crowd Prediction Algorithm

The system uses a trained XGBoost model that considers:
- Day of the week
- Month and season
- Festival flags
- Holiday indicators
- Special events
- Historical footfall data

**Prediction Levels:**
- **Low**: Green indicator, normal capacity
- **Medium**: Yellow indicator, moderate crowd
- **High**: Red indicator, high crowd expected

## 🔧 Troubleshooting

### **Common Issues**

1. **Server won't start**
   - Check if all dependencies are installed
   - Ensure port 5000 is available
   - Verify database file exists

2. **Login fails**
   - Use credentials: admin / admin123
   - Check database connection
   - Verify admin user exists

3. **No data showing**
   - Run `python database.py` to initialize
   - Check database file permissions
   - Verify sample data is loaded

4. **Crowd prediction not working**
   - Ensure model files exist in admin folder
   - Check if encoders are properly loaded
   - Verify historical data is available

## 📝 Development Notes

- **Template Path**: Configured to use `../templates` from admin folder
- **Database Path**: Uses `../pilgrim.db` from admin folder
- **Model Files**: Located in admin folder (`crowd_prediction_model.pkl`)
- **Auto-refresh**: 30-second intervals for real-time updates

## 🎯 Future Enhancements

- Push notifications for emergencies
- Advanced analytics and reporting
- Mobile app integration
- Multi-temple support
- Advanced crowd prediction models
- Integration with external APIs

---

**Admin Dashboard is now fully functional with real-time updates, crowd prediction, and comprehensive management features!** 🎉