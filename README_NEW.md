# 🧬 PharmaGuard 2.0 - Pharmacogenomic Risk Assessment Platform

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/TechHead25/Pharma_TechTitans)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-16+-green.svg)](https://nodejs.org/)

> Advanced AI-powered pharmacogenomic analysis platform with multi-drug support, user authentication, admin dashboard, and data visualization.

## ✨ What's New in v2.0

✅ **Multi-Drug Selection** - Select multiple medications for comprehensive analysis  
✅ **User Authentication** - Secure login/register with JWT tokens  
✅ **Database Storage** - All analyses saved with SQLite  
✅ **Admin Dashboard** - Monitor system statistics and user activity  
✅ **Data Visualization** - Track analysis history and trends  
✅ **Protected Routes** - Role-based access control  

## 🎯 Features

### Core Analysis
- **Multi-Drug Support**: Analyze interactions between multiple medications
- **CPIC-Aligned**: Clinical Pharmacogenetics Implementation Consortium guidelines
- **VCF File Upload**: Support for patient genetic data
- **AI-Powered Explanations**: Dual-layer LLM-generated insights
- **Risk Assessment**: Automatic phenotype detection and risk scoring

### User Features
- **Secure Authentication**: bcrypt password hashing + JWT tokens
- **Analytics Dashboard**: Track your analysis history and trends
- **Data Visualization**: Charts and statistics for your analyses
- **User Records**: All analyses stored securely in database

### Admin Features
- **System Overview**: Total users, analyses, success rates
- **User Management**: View all registered users
- **Drug Analytics**: Most analyzed medications
- **Record Tracking**: Monitor all VCF analyses

## 📋 Requirements

- **Python 3.8+**
- **Node.js 16+**
- **npm or yarn**
- **OpenAI API Key** (for LLM explanations)

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

#### Mac/Linux
```bash
chmod +x quickstart.sh
./quickstart.sh
```

#### Windows
```bash
quickstart.bat
```

### Option 2: Manual Setup

#### 1. Backend Setup
```bash
cd pharmaguard-backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start backend
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup (New Terminal)
```bash
cd pharmaguard-frontend

# Install dependencies
npm install --legacy-peer-deps

# Start development server
npm run dev
```

#### 3. Open Application
```
http://localhost:3003
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) | Detailed setup guide |
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | Complete technical documentation |
| [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) | Full list of enhancements |

## 💻 Project Structure

```
pharmaguard/
├── pharmaguard-backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py                   # API endpoints
│   │   ├── database.py               # SQLAlchemy models
│   │   ├── auth.py                   # JWT authentication
│   │   ├── schemas.py                # Data validation
│   │   ├── engines/                  # RiskAssessmentEngine
│   │   ├── parsers/                  # VCF parser
│   │   └── llm_integration.py        # OpenAI integration
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment template
│   └── pharmaguard.db                # SQLite (auto-created)
│
├── pharmaguard-frontend/             # React/Vite frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx             # User login
│   │   │   ├── Register.jsx          # New user registration
│   │   │   ├── Dashboard.jsx         # Main analysis interface
│   │   │   ├── AdminDashboard.jsx    # Admin panel
│   │   │   └── DataVisualizationDashboard.jsx
│   │   ├── components/
│   │   │   ├── DrugSelector.jsx
│   │   │   ├── VCFUploader.jsx
│   │   │   ├── ResultsDisplay.jsx
│   │   │   └── ProtectedRoute.jsx    # Auth guard
│   │   ├── App.jsx                   # Router setup
│   │   └── index.css                 # Tailwind styles
│   ├── package.json                  # Node dependencies
│   └── vite.config.js                # Vite configuration
│
├── SETUP_INSTRUCTIONS.md             # Quick start
├── IMPLEMENTATION_GUIDE.md           # Full documentation
├── CHANGES_SUMMARY.md                # What's new
├── quickstart.sh                     # Mac/Linux auto-setup
└── quickstart.bat                    # Windows auto-setup
```

## 🔐 Authentication

### Register New Account
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!"
}
```

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

Response includes `access_token` for subsequent API calls.

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login & get token
- `GET /api/v1/auth/me` - Get current user

### Analysis
- `GET /api/v1/drugs` - Get supported drugs (12 medications)
- `POST /api/v1/analyze-vcf` - Analyze VCF file with drugs

### Records (Protected)
- `POST /api/v1/records/save` - Save analysis
- `GET /api/v1/records/user` - Get user's analyses
- `GET /api/v1/records/{id}` - Get analysis details
- `DELETE /api/v1/records/{id}` - Delete analysis

### Admin (Admin Only)
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/users` - List all users
- `GET /api/v1/admin/records` - List all records

### System
- `GET /api/v1/health` - Health check
- `GET /api/v1/drugs` - Supported medications

## 🧪 Testing

### Create Test Account
1. Go to http://localhost:3003
2. Click "Register"
3. Enter credentials and register
4. Login with new account

### Run Analysis
1. Select 1-3 medications (e.g., Codeine, Warfarin)
2. Upload sample VCF file from `pharmaguard-backend/sample_vcf/`
3. Click "Analyze"
4. View multi-drug results

### Access Admin Dashboard
1. Create user account
2. Run setup script to make admin:
   ```python
   from app.database import SessionLocal, User
   db = SessionLocal()
   user = db.query(User).filter(User.email == "your-email@example.com").first()
   user.is_admin = True
   db.commit()
   ```
3. Login and click "Admin" button

## 🎯 Supported Medications (12 Drugs)

1. **Codeine** - Opioid pain reliever (CYP2D6)
2. **Warfarin** - Anticoagulant (CYP2C19, CYP2C9)
3. **Clopidogrel** - Antiplatelet agent (CYP2C19)
4. **Simvastatin** - Cholesterol management (SLCO1B1)
5. **Azathioprine** - Immunosuppressant (TPMT)
6. **Fluorouracil** - Chemotherapy agent (DPYD)
7. **Metoprolol** - Beta-blocker (CYP2D6)
8. **Atenolol** - Hypertension management (CYP2D6)
9. **Sertraline** - Antidepressant SSRI (CYP2D6, CYP2C19)
10. **Escitalopram** - SSRI antidepressant (CYP2C19)
11. **Topiramate** - Anticonvulsant (CYP2D6)
12. **Phenytoin** - Seizure prevention (CYP2C19, CYP2C9)

## 🔒 Security

### Implemented
✅ Bcrypt password hashing  
✅ JWT token-based authentication  
✅ Role-based access control  
✅ HTTPS-ready CORS configuration  
✅ Input validation with Pydantic  
✅ Protected API endpoints  

### Production Recommendations
- Change `SECRET_KEY` in .env
- Use environment-specific settings
- Enable HTTPS/SSL
- Set secure cookie flags
- Implement rate limiting
- Use strong password requirements
- Add CSRF protection
- Regular security audits

## 📈 Performance

- Optimized database queries
- Efficient component rendering
- RESTful API design
- Caching ready
- Async/await for I/O operations

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000
```

### Module Not Found
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install --legacy-peer-deps
npm install react-router-dom
```

### CORS Error
Ensure both servers are running:
- Backend: http://localhost:8000
- Frontend: http://localhost:3003

### Database Error
```bash
# Delete old database and restart
rm pharmaguard-backend/pharmaguard.db
python -m uvicorn app.main:app --reload --port 8000
```

## 📝 Environment Variables

### Backend (.env)
```ini
SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=sk-your-openai-api-key
CORS_ALLOWED_ORIGINS=http://localhost:3003
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 👥 Team

**PharmaGuard Team** - Pharmacogenomic Risk Assessment Platform

## 📞 Support

- Check documentation files
- Review API endpoints
- Check browser console (F12)
- Review backend terminal logs

## 🔄 Update Log

### v2.0 (Current)
- ✅ Multi-drug selection fixed
- ✅ User authentication added
- ✅ Database support (SQLite)
- ✅ Admin dashboard
- ✅ Data visualization
- ✅ Protected routes
- ✅ 20+ new API endpoints

### v1.0
- Initial pharmacogenomic analysis engine
- Single drug analysis
- VCF file parsing
- CPIC guideline implementation

## 🎓 Educational Resources

- [CPIC Guidelines](https://cpicpgx.org/)
- [Pharmacogenomics](https://en.wikipedia.org/wiki/Pharmacogenomics)
- [VCF Format](https://samtools.github.io/hts-specs/VCFv4.2.pdf)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## ⚖️ Disclaimer

This tool is for **educational and informational purposes only**. It should not replace professional medical advice. Always consult with a healthcare provider before making medication decisions.

---

<div align="center">

**PharmaGuard 2.0** powered by ✨ AI & ⚕️ Clinical Guidelines

[Documentation](IMPLEMENTATION_GUIDE.md) • [Setup Guide](SETUP_INSTRUCTIONS.md) • [GitHub](https://github.com/TechHead25/Pharma_TechTitans)

Made with ❤️ for better healthcare

</div>
