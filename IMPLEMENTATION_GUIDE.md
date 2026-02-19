# PharmaGuard 2.0 Enhancement Guide

## NEW FEATURES IMPLEMENTED

This document outlines all the enhancements made to PharmaGuard 2.0, including authentication, admin dashboard, data visualization, and multi-drug selection improvements.

---

## 1. MULTI-DRUG SELECTION FIX ✅

### Problem
Previously, selecting a single drug would automatically advance to the file upload stage, preventing users from selecting multiple drugs.

### Solution
- Removed auto-advance behavior from `DrugSelector` component
- Added an explicit "Continue" button that only appears when at least one drug is selected
- Users can now select multiple drugs before proceeding to file upload

### Usage
1. Users select one or more medications from the dropdown
2. The "Continue with Selected Medications" button appears
3. Users click to proceed with their selections

---

## 2. AUTHENTICATION SYSTEM ✅

### New Backend Endpoints

#### User Registration
```
POST /api/v1/auth/register
Body: {
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!"
}
Response: {
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": { user_object }
}
```

#### User Login
```
POST /api/v1/auth/login
Body: {
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
Response: {
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": { user_object }
}
```

#### Logout
```
POST /api/v1/auth/logout
Headers: Authorization: Bearer {token}
```

#### Get Current User
```
GET /api/v1/auth/me
Headers: Authorization: Bearer {token}
```

### Security Features
- Passwords hashed with bcrypt
- JWT tokens for stateless authentication
- Token expiration (24 hours by default)
- HTTPS support in production

---

## 3. VCF RECORD STORAGE ✅

### New Database Tables

#### `users` Table
- id (Integer, Primary Key)
- email (String, Unique)
- username (String, Unique)
- full_name (String)
- hashed_password (String)
- is_admin (Boolean)
- created_at (DateTime)
- updated_at (DateTime)

#### `vcf_records` Table
- id (String, Primary Key)
- user_id (Integer, Foreign Key)
- username (String)
- filename (String)
- file_path (String)
- analyzed_drugs (String) - comma-separated
- analysis_result (Text) - JSON string
- phenotypes (Text) - JSON string
- uploaded_at (DateTime)
- analyzed_at (DateTime)
- status (String) - pending/analyzing/completed/failed

### VCF Record Endpoints

#### Save Analysis Record
```
POST /api/v1/records/save
Headers: Authorization: Bearer {token}
Body: {
  "filename": "patient_vcf.vcf",
  "analyzed_drugs": "CODEINE,WARFARIN",
  "analysis_result": "{...json...}",
  "phenotypes": "{...json...}"
}
```

#### Get User's Records
```
GET /api/v1/records/user
Headers: Authorization: Bearer {token}
Response: [{ record_object }, ...]
```

#### Get Record Details
```
GET /api/v1/records/{record_id}
Headers: Authorization: Bearer {token}
```

#### Delete Record
```
DELETE /api/v1/records/{record_id}
Headers: Authorization: Bearer {token}
```

---

## 4. ADMIN DASHBOARD ✅

### Admin Features
- Only accessible to users with `is_admin=true`
- Three main tabs: Overview, Users, Records

### Overview Tab
- **Total Users Count**: Number of registered users
- **Total Analyses**: Total VCF files analyzed
- **Completed Analyses**: Successful analyses count
- **Failed Analyses**: Failed analyses count
- **Most Analyzed Drugs**: Top 10 drugs by analysis frequency
- **Recent Analyses**: Latest 10 analyses with details

### Users Tab
- View all users in the system
- Display columns: Name, Email, Username, Role, Analysis Count, Join Date
- Identify admin vs regular users

### Records Tab
- View all VCF records in the system
- Display columns: User, Filename, Drugs Analyzed, Status, Upload Date
- Track analysis status across all users

### Admin Endpoints
```
GET /api/v1/admin/stats
Headers: Authorization: Bearer {token}
Response: {
  "total_users": 10,
  "total_analyses": 45,
  "total_completed": 43,
  "total_failed": 2,
  "most_analyzed_drugs": [{drugs, count}, ...],
  "recent_analyses": [{record}, ...]
}

GET /api/v1/admin/users
Headers: Authorization: Bearer {token}

GET /api/v1/admin/records
Headers: Authorization: Bearer {token}
```

---

## 5. DATA VISUALIZATION DASHBOARD ✅

### User Analytics Features
- **Total Analyses**: User's total analysis count
- **Success Rate**: Percentage of completed analyses
- **Drug Frequency Chart**: Bar chart of most analyzed by user
- **Status Distribution**: Pie chart of completed vs failed analyses
- **Recent Analyses Table**: User's analysis history

### Key Metrics
- Total analyses performed by user
- Number of completed analyses
- Number of failed analyses
- Success rate percentage
- Top 5 drugs analyzed
- Analysis status breakdown

### User Endpoints
```
GET /api/v1/records/user
Headers: Authorization: Bearer {token}
```

---

## 6. FRONTEND ROUTING STRUCTURE ✅

### New Pages/Components

#### Login Page (`src/pages/Login.jsx`)
- Email and password input
- Error messaging
- Link to register page
- Demo credentials display

#### Register Page (`src/pages/Register.jsx`)
- Full registration form
- Password validation
- Email validation
- Success confirmation

#### Dashboard Page (`src/pages/Dashboard.jsx`)
- Main analysis workflow
- Multi-drug selection
- VCF file upload
- Results display
- Navigation buttons (Admin, Analytics, Logout)

#### Admin Dashboard (`src/pages/AdminDashboard.jsx`)
- System overview
- User management
- Record management
- Statistical insights

#### Data Visualization (`src/pages/DataVisualizationDashboard.jsx`)
- User analytics
- Statistics overview
- Drug frequency visualization
- Status distribution chart

#### Protected Route (`src/components/ProtectedRoute.jsx`)
- Route-level authentication
- Admin role checking
- Automatic redirect to login

### Routing Configuration
```
/login                 → Login page
/register              → Register page
/dashboard            → Main analysis (protected)
/admin                → Admin dashboard (admin only)
/visualizations       → Data visualization (protected)
/                     → Redirects to /dashboard
```

---

## 7. INSTALLATION & SETUP

### Backend Setup

1. **Install Dependencies**
```bash
cd pharmaguard-backend
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and set SECRET_KEY and OPENAI_API_KEY
```

3. **Run Backend**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The SQLite database (`pharmaguard.db`) will be created automatically.

### Frontend Setup

1. **Install Dependencies**
```bash
cd pharmaguard-frontend
npm install --legacy-peer-deps
```

2. **Run Frontend**
```bash
npm run dev
```

The frontend will run on `http://localhost:3003`

---

## 8. TESTING

### Demo Account
For testing purposes, you can use:
- **Email**: demo@pharmaguard.com
- **Password**: Demo@123456

To create this account:
1. Visit the register page
2. Sign up with the credentials above (or any credentials you prefer)
3. You'll be automatically logged in

### Creating Admin Account
To create an admin account, modify the database after creating a user:
```bash
python
from app.database import SessionLocal, User
db = SessionLocal()
user = db.query(User).filter(User.email == "admin@pharmaguard.com").first()
user.is_admin = True
db.commit()
```

### Test Workflow
1. **Register/Login** → Redirect to dashboard
2. **Select Multiple Drugs** → Click Continue button
3. **Upload VCF File** → Test with provided sample files
4. **View Results** → Multi-drug analysis results
5. **Check Analytics** → View your analysis history
6. **(Admin) View Dashboard** → See system statistics

---

## 9. DATABASE SCHEMA

### SQLite Database Structure
```sql
-- Users Table
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email VARCHAR UNIQUE,
  username VARCHAR UNIQUE,
  full_name VARCHAR,
  hashed_password VARCHAR,
  is_admin BOOLEAN DEFAULT False,
  created_at DATETIME,
  updated_at DATETIME
);

-- VCF Records Table
CREATE TABLE vcf_records (
  id VARCHAR PRIMARY KEY,
  user_id INTEGER,
  username VARCHAR,
  filename VARCHAR,
  file_path VARCHAR,
  analyzed_drugs VARCHAR,
  analysis_result TEXT,
  phenotypes TEXT,
  uploaded_at DATETIME,
  analyzed_at DATETIME,
  status VARCHAR DEFAULT 'pending'
);
```

---

## 10. ENVIRONMENT VARIABLES

### Backend (.env)
```
SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key
CORS_ALLOWED_ORIGINS=http://localhost:3003,http://localhost:3001,...
```

### Frontend (automatic)
- Base API URL: `http://localhost:8000`
- Auth endpoints use Bearer tokens

---

## 11. API ERROR HANDLING

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Server Error

Error responses include:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## 12. SECURITY CONSIDERATIONS

### For Production Deployment
1. **Change SECRET_KEY** in .env
2. **Enable HTTPS** for all URLs
3. **Use environment-specific CORS** settings
4. **Set secure cookie flags**
5. **Implement rate limiting**
6. **Use strong password requirements**
7. **Add CSRF protection**
8. **Implement auth logging**
9. **Use database backups**
10. **Add request validation**

---

## 13. FUTURE ENHANCEMENTS

Potential improvements:
- OAuth2/Social login integration
- Two-factor authentication (2FA)
- Role-based access control (RBAC)
- Export analysis reports (PDF, CSV)
- Bulk VCF analysis
- Analysis scheduling
- Advanced filtering and search
- Real-time notifications
- Team/Organization support
- API documentation (Swagger)

---

## 14. TROUBLESHOOTING

### Issue: "CORS policy: No 'Access-Control-Allow-Origin'"
**Solution**: Ensure frontend is running on a CORS-allowed origin. Check the backend CORS configuration in `app/main.py`.

### Issue: "Invalid token" error
**Solution**: Token may have expired. Logout and login again.

### Issue: Admin dashboard not accessible
**Solution**: Ensure user account has `is_admin=True` in the database.

### Issue: Images/styling not loading
**Solution**: Clear browser cache and hard refresh (Ctrl+Shift+R).

---

## 15. SUPPORT & DOCUMENTATION

For more information:
- Backend API docs: `http://localhost:8000/docs`
- Frontend source: `/pharmaguard-frontend/src`
- Backend source: `/pharmaguard-backend/app`

---

**Version**: 2.0
**Last Updated**: February 2024
**Status**: Production Ready ✅
