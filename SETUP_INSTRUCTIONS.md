# PharmaGuard 2.0 - Quick Start Guide

## 🚀 What's New

Your PharmaGuard 2.0 has been upgraded with several powerful features:

✅ **Fixed Multi-Drug Selection** - Select multiple drugs before proceeding  
✅ **User Authentication** - Login/Register system with JWT  
✅ **VCF Record Storage** - All analyses stored in database  
✅ **Admin Dashboard** - Monitor system statistics and user activity  
✅ **Data Visualization** - Track your analysis history and trends  

---

## 📋 Prerequisites

- Python 3.8+ 
- Node.js 16+
- npm or yarn

---

## 🛠️ Installation

### Step 1: Backend Setup

```bash
cd pharmaguard-backend

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Important: Edit .env and add your OpenAI API key
# nano .env  (or use your editor)
```

**Key .env variables to set:**
```
SECRET_KEY=your-secret-key-change-in-production-12345
OPENAI_API_KEY=sk-your-openai-key-here
```

### Step 2: Frontend Setup

```bash
cd pharmaguard-frontend

# Install Node dependencies
npm install --legacy-peer-deps

# The app will use http://localhost:8000 for API calls
```

---

## ▶️ Running the Application

### Terminal 1: Start Backend

```bash
cd pharmaguard-backend
python -m uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Terminal 2: Start Frontend

```bash
cd pharmaguard-frontend
npm run dev
```

**Expected output:**
```
VITE v5.0.0  ready in XXX ms

➜  Local:   http://localhost:3003/
```

### Access the Application

1. Open your browser to: **http://localhost:3003**
2. You'll be redirected to the login page
3. Click "Register" to create a new account
4. Use any credentials (email, username, password)

---

## 🎯 Using the Application

### Workflow Overview

1. **Login/Register**
   - Create a new account or login with existing credentials
   - Account is automatically stored in the database

2. **Select Medications**
   - Choose 1 or more drugs from the dropdown
   - Search by name, category, or gene
   - Click "Continue with Selected Medications"

3. **Upload VCF File**
   - Upload a patient VCF file
   - Click "Analyze Pharmacogenomic Profile"

4. **View Results**
   - See analysis for each selected drug
   - View CPIC-aligned recommendations
   - Get AI-powered explanations

5. **Analytics**
   - Click the "Analytics" button to view your analysis history
   - See charts and statistics
   - Track your most analyzed drugs

---

## 👨‍💼 Admin Dashboard

### Accessing Admin Dashboard

1. Your account needs `is_admin=True` in the database
2. Click the "Admin" button in the header
3. View:
   - **Overview**: System statistics
   - **Users**: All registered users
   - **Records**: All VCF analyses

### Creating an Admin Account

After registering, run this Python script:

```python
from app.database import SessionLocal, User

db = SessionLocal()
user = db.query(User).filter(User.email == "your-email@example.com").first()
if user:
    user.is_admin = True
    db.commit()
    print("Admin privileges granted!")
else:
    print("User not found")
```

---

## 🧪 Test Data

### Sample VCF Files

Test files are available in `pharmaguard-backend/sample_vcf/`:
- `patient_cyp2d6_pm.vcf` - Poor metabolizer phenotype
- `patient_cyp2c19_em.vcf` - Extensive metabolizer
- `patient_multi_gene.vcf` - Multiple gene variants

### Demo Workflow

1. Login/Register
2. Select: **Codeine** and **Warfarin**
3. Upload: `patient_cyp2d6_pm.vcf`
4. Analyze and view results
5. Check analytics for your analysis history

---

## 🔐 Authentication

### JWT Token Management

- Tokens stored in browser's localStorage
- Expiration: 24 hours
- Auto-logout when expired
- Logout button clears token

### Protected Routes

- `/dashboard` - Main analysis (requires login)
- `/admin` - Admin panel (requires admin role)
- `/visualizations` - Analytics (requires login)
- `/login` - Public
- `/register` - Public

---

## 📊 Database

### SQLite Location

- **Backend**: `pharmaguard-backend/pharmaguard.db`
- **Tables**: users, vcf_records
- **Auto-created** on first run

### Accessing Database

```bash
sqlite3 pharmaguard.db

# View users
SELECT id, email, username, is_admin FROM users;

# View VCF records
SELECT * FROM vcf_records LIMIT 10;
```

---

## 🚨 Troubleshooting

### Port Already in Use

If port 3003 or 8000 is already in use:

```bash
# Find process using port 8000
lsof -i :8000  (Mac/Linux)
netstat -ano | findstr :8000  (Windows)

# Kill process or use different port
python -m uvicorn app.main:app --reload --port 8001
```

### CORS Error: "Access to fetch has been blocked"

**Solution**: Ensure both servers are running:
- Backend on port 8000
- Frontend on port 3003

### "Module not found" Error

```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install --legacy-peer-deps
npm install react-router-dom
```

### Authentication Issues

1. Clear browser localStorage:
   - Open DevTools (F12)
   - Go to Application > Local Storage
   - Delete all entries
   - Refresh page and login again

---

## 📁 Project Structure

```
pharmaguard/
├── pharmaguard-backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + auth endpoints
│   │   ├── database.py        # SQLAlchemy models
│   │   ├── auth.py            # JWT & password utilities
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── engines/
│   │   ├── parsers/
│   │   └── llm_integration.py
│   ├── requirements.txt
│   └── pharmaguard.db         # SQLite database (auto-created)
│
├── pharmaguard-frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DrugSelector.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   └── DataVisualizationDashboard.jsx
│   │   ├── App.jsx            # Routing setup
│   │   └── main.jsx
│   └── package.json
│
└── IMPLEMENTATION_GUIDE.md    # Full documentation
```

---

## 🔑 Environment Variables

### Backend (.env)

```ini
# Security
SECRET_KEY=your-secret-key-change-in-production-12345

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Server
HOST=0.0.0.0
PORT=8000

# CORS (frontend URLs)
CORS_ALLOWED_ORIGINS=http://localhost:3003,http://localhost:5173

# Database (auto-created if not specified)
# Leave blank for SQLite
```

---

## ✨ Features at a Glance

| Feature | Endpoint | Protected | Description |
|---------|----------|-----------|-------------|
| Register | POST /auth/register | ❌ | Create new account |
| Login | POST /auth/login | ❌ | Login & get token |
| Dashboard | GET /dashboard | ✅ | Main analysis page |
| Analytics | GET /visualizations | ✅ | View your statistics |
| Admin | GET /admin/stats | ✅👮 | System statistics |
| Save Record | POST /records/save | ✅ | Store analysis |
| Get Records | GET /records/user | ✅ | User's analyses |
| Analyze VCF | POST /analyze-vcf | ✅ | Run analysis |

Legend: ❌ = Public, ✅ = Auth Required, 👮 = Admin Only

---

## 📞 Support

For issues or questions:
1. Check IMPLEMENTATION_GUIDE.md for detailed docs
2. Review error messages in browser console (F12)
3. Check backend logs in terminal
4. Verify both servers are running on correct ports

---

## 🎉 You're All Set!

Your PharmaGuard 2.0 is ready to use with:
- ✅ Secure authentication
- ✅ Multi-drug analysis
- ✅ Data persistence
- ✅ Admin oversight
- ✅ Analytics & insights

**Happy analyzing!** 🧬

---

**Last Updated**: February 2024  
**Version**: 2.0
