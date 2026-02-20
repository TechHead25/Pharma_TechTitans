# Frontend Deployment Guide (Vercel)

## Prerequisites
1. ✅ Frontend code pushed to GitHub
2. ✅ Backend deployed on Render
3. ⚠️  Backend URL from Render (e.g., `https://pharmaguard-backend-xxxx.onrender.com`)

## Deployment Methods

### Method 1: Vercel Dashboard (Easiest)

#### Step 1: Sign In
1. Go to [vercel.com](https://vercel.com)
2. Click "Sign Up" or "Log In"
3. Choose "Continue with GitHub"
4. Authorize Vercel to access your repositories

#### Step 2: Import Project
1. Click "Add New..." → "Project"
2. Find and select `TechHead25/Pharma_TechTitans` repository
3. Click "Import"

#### Step 3: Configure Build Settings
Vercel should auto-detect everything, but verify:

- **Framework Preset**: Vite
- **Root Directory**: `pharmaguard-frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

#### Step 4: Set Environment Variables
Click on "Environment Variables" section:

| Key | Value | Example |
|-----|-------|---------|
| `VITE_API_URL` | Your Render backend URL | `https://pharmaguard-backend-abc123.onrender.com` |

**Important**: Use your actual backend URL from Render, NOT the example above!

To get your backend URL:
1. Go to your Render dashboard
2. Click on your backend service
3. Copy the URL (looks like: `https://pharmaguard-backend-xxxx.onrender.com`)
4. Paste it as the `VITE_API_URL` value in Vercel

#### Step 5: Deploy
1. Click "Deploy" button
2. Wait 2-3 minutes for build to complete
3. You'll get a URL like: `https://pharma-tech-titans.vercel.app`

---

### Method 2: Vercel CLI (Advanced)

#### Step 1: Install Vercel CLI
```powershell
npm install -g vercel
```

#### Step 2: Login to Vercel
```powershell
vercel login
```

#### Step 3: Navigate to Frontend Directory
```powershell
cd pharmaguard-frontend
```

#### Step 4: Deploy
```powershell
# For first deployment
vercel

# Follow the prompts:
# - Set up and deploy? Y
# - Which scope? (your account)
# - Link to existing project? N
# - Project name? pharmaguard-frontend
# - Directory? ./
# - Override settings? N
```

#### Step 5: Set Environment Variable
```powershell
# Replace YOUR_BACKEND_URL with your actual Render URL
vercel env add VITE_API_URL production
# When prompted, paste: https://pharmaguard-backend-xxxx.onrender.com
```

#### Step 6: Deploy to Production
```powershell
vercel --prod
```

---

## Post-Deployment Checklist

### 1. Verify Backend URL
Test your backend is accessible:
- Go to: `https://your-backend-url.onrender.com/api/v1/health`
- Should return: `{"status":"healthy"}`

### 2. Test Frontend
1. Visit your Vercel URL (e.g., `https://pharma-tech-titans.vercel.app`)
2. Try to register a new account
3. Try to login
4. Upload a VCF file
5. Check if drug interaction analysis works

### 3. Common Issues

#### Issue: "Failed to fetch" or "Network Error"
**Cause**: Incorrect backend URL or CORS issue

**Solution**:
1. Check environment variable in Vercel dashboard
2. Ensure backend URL doesn't have trailing slash
3. Verify backend CORS settings allow frontend domain

#### Issue: "502 Bad Gateway" or Backend Errors
**Cause**: Backend not fully deployed or crashed

**Solution**:
1. Check Render backend logs
2. Ensure all environment variables set in Render:
   - `GEMINI_API_KEY`
   - `SECRET_KEY`
   - `DATABASE_URL` (optional)

#### Issue: Build Failed on Vercel
**Cause**: Missing dependencies or build errors

**Solution**:
1. Check build logs in Vercel dashboard
2. Ensure `package.json` is correct
3. Try running `npm run build` locally first

---

## Environment Variables Reference

### Frontend (Vercel)
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | ✅ Yes | Backend API URL | `https://pharmaguard-backend-abc.onrender.com` |

### Backend (Render)
| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key |
| `SECRET_KEY` | ✅ Yes | JWT secret for authentication |
| `DATABASE_URL` | ⚠️  Optional | PostgreSQL connection string |

---

## Update Deployment

### Update Frontend
1. **Automatic**: Push to GitHub main branch
   - Vercel auto-deploys on every push

2. **Manual**: Redeploy in Vercel dashboard
   - Go to Vercel dashboard
   - Click "Deployments" tab
   - Click "..." → "Redeploy"

### Update Environment Variables
1. Go to Vercel project dashboard
2. Click "Settings" → "Environment Variables"
3. Edit or add variables
4. Redeploy (automatic or manual)

---

## Custom Domain (Optional)

### Add Custom Domain
1. Go to Vercel project → "Settings" → "Domains"
2. Add your domain (e.g., `pharmaguard.com`)
3. Follow DNS configuration instructions
4. Vercel automatically provisions SSL certificate

---

## Monitoring & Logs

### View Logs
1. Go to Vercel dashboard
2. Click on your deployment
3. Click "Logs" tab
4. See real-time build and runtime logs

### Analytics
Vercel provides free analytics:
- Go to "Analytics" tab
- See page views, performance, etc.

---

## Quick Reference

### Get Backend URL from Render
```
1. Login to Render dashboard
2. Click your backend service
3. Copy URL from top of page
```

### Deploy to Vercel (Dashboard)
```
vercel.com → Add New → Project → Import → Deploy
```

### Deploy to Vercel (CLI)
```powershell
cd pharmaguard-frontend
vercel login
vercel --prod
```

---

## Next Steps

After deployment:
1. ✅ Test all features (register, login, upload VCF, analyze)
2. ✅ Share frontend URL with team
3. ✅ Optional: Set up custom domain
4. ✅ Optional: Enable Vercel Analytics

Your app should now be live! 🚀

**Frontend URL**: Check Vercel dashboard
**Backend URL**: Check Render dashboard
