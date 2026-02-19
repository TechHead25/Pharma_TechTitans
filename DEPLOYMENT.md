# PharmaGuard Deployment Guide

## 🚀 Quick Start for Development

### Backend (Local)
```bash
cd pharmaguard-backend
pip install -r requirements.txt
python run_backend.py
# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Frontend (Local)
```bash
cd pharmaguard-frontend
npm install
npm run dev
# App runs at http://localhost:3000
```

---

## 📤 Deploying Frontend to Vercel

### Method 1: GitHub Integration (Recommended)
1. Push code to GitHub repository
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click "Add New Project"
4. Import your Git repository
5. Select `pharmaguard-frontend` as the root directory
6. Add environment variables:
   ```
   VITE_API_URL=https://your-backend-url.vercel.app
   ```
7. Click "Deploy"

**Deployment is automatic on every push to main branch**

### Method 2: Vercel CLI
```bash
cd pharmaguard-frontend
npm install -g vercel
vercel login
vercel --prod
```

### Post-Deployment
- Frontend URL: `https://pharmaguard-frontend.vercel.app` (or your custom domain)
- Ensure backend API URL is correctly configured in environment variables

---

## 🖥️ Deploying Backend to Render (with PostgreSQL)

### 1. Using Render Blueprint (Recommended - Automatic)
The repository includes a `render.yaml` blueprint that sets up the backend with PostgreSQL automatically.

**Steps:**
1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Blueprint"
4. Paste your repo URL or connect GitHub account
5. Render will auto-create:
   - Web Service (Python backend)
   - PostgreSQL database instance
   - Auto-configured `DATABASE_URL` environment variable
6. Add environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)
7. Click "Deploy"

**Result:**
- Backend URL: `https://pharmaguard-backend.onrender.com`
- API docs: `https://pharmaguard-backend.onrender.com/docs`
- PostgreSQL database runs alongside in same blueprint
- Auto-migrations on deploy via SQLAlchemy `Base.metadata.create_all()`

---

### 2. Manual Setup (If Blueprint Not Used)

**Web Service:**
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `pharmaguard-backend`
   - **Root Directory**: `pharmaguard-backend`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r requirements-deploy.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app.main:app --timeout 120`

**PostgreSQL Database:**
1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `pharmaguard-db`
   - **PostgreSQL Version**: Latest
3. Render will generate connection string in format: `postgresql://user:password@host:5432/database_name`

**Connect Database to Web Service:**
1. Go to Web Service settings
2. Add environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the PostgreSQL connection string from the database instance

**Add Secret Variables:**
```
OPENAI_API_KEY=your-api-key-here
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-in-production
```

**Deploy:**
- Click "Deploy" button or enable auto-deploy for main branch commits

---

### 3. Environment Variables for Render Deployment

On Render dashboard, ensure these are set:

```
DATABASE_URL=postgresql://username:password@host:5432/database_name
OPENAI_API_KEY=sk-xxxx...
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-frontend.onrender.com
```

---

### 4. Local Development Reference

For **local testing with PostgreSQL**, set environment variables in `.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/pharmaguard_local
```

For **local SQLite** (default), leave `DATABASE_URL` empty or unset:
```
# Falls back to sqlite:///./pharmaguard.db
```

---

## 🖥️ Deploying Backend to Render

### Setup Steps
1. Push code to GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure service:
   - **Name**: `pharmaguard-backend`
   - **Root Directory**: `pharmaguard-backend`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r requirements-deploy.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app.main:app --timeout 120`

6. Add environment variables in Render dashboard:
   ```
   OPENAI_API_KEY=your-api-key-here
   FLASK_ENV=production
   ```

7. Deploy by clicking "Deploy"

### Auto-Deploy
Enable auto-deploy when Render detects commits to the main branch.

### API Endpoint
- Backend URL: `https://pharmaguard-backend.onrender.com`
- API docs: `https://pharmaguard-backend.onrender.com/docs`

---

## 🚀 Deploying Backend to Railway

### Setup Steps
1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize and select your repository
5. Railway auto-detects Python app
6. Configure:
   - Set the root directory to `pharmaguard-backend`
   - Ensure requirements-deploy.txt is used

7. Add environment variables in Railway dashboard:
   ```
   OPENAI_API_KEY=your-api-key-here
   FLASK_ENV=production
   PORT=8000
   ```

8. Deploy automatically triggers

### API Endpoint
- Backend URL: `https://your-project.railway.app`
- API docs: `https://your-project.railway.app/docs`

---

## 📋 Environment Setup Checklist

### Frontend (.env.local)
```
VITE_API_URL=https://your-backend-url.app
```

### Backend (.env)
```
OPENAI_API_KEY=sk-xxxx...
FLASK_ENV=production
DEBUG=False
ALLOWED_ORIGINS=https://your-frontend-url.app,https://your-frontend-url.vercel.app
MAX_VCF_SIZE_MB=5
```

---

## ✅ Post-Deployment Testing

### Test Frontend
1. Navigate to deployed frontend URL
2. Upload a sample VCF file
3. Verify results display with color coding
4. Test "Copy JSON" button
5. Verify expandable detail sections work

### Test Backend
```bash
# Health check
curl https://your-backend-url.app/api/v1/health

# Test with sample VCF
curl -X POST -F "file=@sample.vcf" https://your-backend-url.app/api/v1/analyze-vcf
```

### Monitor Logs
- **Vercel**: Dashboard → Deployments → Logs
- **Render**: Dashboard → Web Service → Logs
- **Railway**: Dashboard → Project → Deployments → Logs

---

## 🔧 Troubleshooting

### Frontend Build Issues
- Clear `.next` or `dist` folder: `rm -r dist`
- Reinstall dependencies: `rm -r node_modules && npm install`
- Check Node version: `node -v` (should be 18+)

### Backend Startup Issues
- Check dependencies: `pip list | grep fastapi`
- Verify Python version: `python --version` (should be 3.10+)
- Check environment variables: `echo $OPENAI_API_KEY`

### CORS Errors
- Update `ALLOWED_ORIGINS` in backend config
- Ensure frontend URL is whitelisted
- Check CORS middleware settings in `app/main.py`

### API Timeout Issues
- Increase timeout for large VCF files
- Check Render/Railway timeout settings
- Monitor backend logs for errors

---

## 📊 Performance Optimization

### Frontend
- Enable compression in Vercel settings
- Cache static assets
- Lazy load components

### Backend  
- Use gunicorn with 4 workers for Render/Railway
- Enable gzip compression
- Cache VCF parsing results (future improvement)

---

## 🔐 Security Checklist

- ✅ Set `DEBUG=False` in production
- ✅ Use HTTPS only (enforced by Vercel/Render)
- ✅ Rotate API keys periodically
- ✅ Use environment variables for secrets
- ✅ Enable CORS only for trusted domains
- ✅ Validate VCF file size (5 MB limit)
- ✅ Sanitize user inputs

---

## 📞 Support & Debugging

### Get Deployment URLs
```bash
# Vercel
vercel list

# Railway
railway status

# Render 
# Check dashboard for service URL
```

### View Live Logs
```bash
# Railway
railway logs

# Render
# Check web dashboard logs section
```

### Rollback Deployment
- **Vercel**: Click deployment → "Rollback"
- **Railway**: Select previous deployment
- **Render**: Redeploy from Git

---

## 🎉 Deployment Success!

Your PharmaGuard application should now be:
- **Frontend**: Live on Vercel
- **Backend**: Live on Render/Railway  
- **APIs**: Accessible and responding
- **Database**: Ready for production use (if implemented)

**Share your deployment links:**
- Frontend: `[Your Vercel URL]`
- Backend API Docs: `[Your Backend URL]/docs`
- GitHub Repo: `[Your GitHub Link]`
