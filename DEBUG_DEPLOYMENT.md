# Deployment Debugging Guide

## Step 1: Verify Backend is Running

Open a new browser tab and visit:
```
https://pharma-techtitans.onrender.com/api/v1/health
```

**Expected Response:**
```json
{"status":"healthy"}
```

**If you get an error:**
- Backend is not running on Render
- Go to Render dashboard → Check logs
- Look for deployment errors

---

## Step 2: Test Registration Endpoint Directly

Open browser console (F12) and paste this:

```javascript
fetch('https://pharma-techtitans.onrender.com/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'test@example.com',
    username: 'testuser',
    full_name: 'Test User',
    password: 'testpassword123',
    confirm_password: 'testpassword123'
  })
})
.then(res => res.json())
.then(data => console.log('Response:', data))
.catch(err => console.error('Error:', err));
```

**Expected:**
- Success response with access_token
- Or specific error message

---

## Step 3: Check Vercel Environment Variable

In browser console on your Vercel site:
```javascript
console.log('API URL:', import.meta.env.VITE_API_URL);
```

**Expected Output:**
```
API URL: https://pharma-techtitans.onrender.com
```

**If it shows `undefined`:**
- Environment variable not set correctly in Vercel
- Go to Vercel → Settings → Environment Variables
- Make sure `VITE_API_URL` is set for **Production**
- Redeploy after adding

---

## Step 4: Check Browser Network Tab

1. Open DevTools (F12)
2. Go to **Network** tab
3. Try to register
4. Look for the registration request
5. Share the error details:
   - Status code (e.g., 404, 500, CORS error)
   - Response body
   - Request URL (should be pharma-techtitans.onrender.com)

---

## Step 5: Check Render Backend Logs

1. Go to: https://dashboard.render.com
2. Click your backend service
3. Click **Logs** tab
4. Try to register on frontend
5. Watch for errors in real-time

Common errors:
- `DATABASE_URL not set` → Need to add PostgreSQL URL
- `GEMINI_API_KEY not set` → Need to add API key
- `SECRET_KEY not set` → Need to add JWT secret

---

## Step 6: Verify CORS Headers

In browser console on registration page:
```javascript
fetch('https://pharma-techtitans.onrender.com/api/v1/drugs')
  .then(res => {
    console.log('CORS Headers:', res.headers);
    console.log('Status:', res.status);
    return res.json();
  })
  .then(data => console.log('Data:', data))
  .catch(err => console.error('CORS Error:', err));
```

**If you see CORS error:**
- Backend CORS not allowing your Vercel domain
- Need to update CORS configuration

---

## Most Common Issues:

### Issue 1: Backend Not Deployed
**Symptom:** 502/503 errors, "Service Unavailable"
**Solution:** 
- Check Render dashboard
- Ensure deployment completed successfully
- Check for build errors in Render logs

### Issue 2: Missing Environment Variables
**Symptom:** Backend starts but crashes immediately
**Solution:**
Go to Render → Environment Variables and add:
```
GEMINI_API_KEY = your-api-key
SECRET_KEY = your-jwt-secret
DATABASE_URL = (optional, falls back to SQLite)
```

### Issue 3: CORS Blocked
**Symptom:** Browser console shows "CORS policy" error
**Solution:** 
- Already fixed in code (commit 70766b1)
- Make sure Render deployed latest code
- Check deployment time vs push time

### Issue 4: Wrong Environment Variable in Vercel
**Symptom:** Network tab shows requests going to localhost
**Solution:**
- Vercel → Settings → Environment Variables
- Add `VITE_API_URL` = `https://pharma-techtitans.onrender.com`
- **Important:** Select all three: Production, Preview, Development
- Redeploy

---

## Quick Test Commands

### Test 1: Backend Health
```bash
curl https://pharma-techtitans.onrender.com/api/v1/health
```

### Test 2: Get Drugs List
```bash
curl https://pharma-techtitans.onrender.com/api/v1/drugs
```

### Test 3: Test Registration
```bash
curl -X POST https://pharma-techtitans.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "password123",
    "confirm_password": "password123"
  }'
```

---

## Report Back With:

Please share:
1. ✅ Health check response: `/api/v1/health`
2. ✅ Browser console errors (screenshot)
3. ✅ Network tab - what URL is being called
4. ✅ Render deployment status
5. ✅ Render environment variables (just names, not values)

This will help me pinpoint the exact issue!
