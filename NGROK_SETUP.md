# Ngrok Setup Instructions (Fixed)

## Current Setup
- **Frontend**: https://guided-kite-heartily.ngrok-free.app (static domain)
- **Backend**: https://9c99575b6efd.ngrok-free.app (configured in ngrok.yml)

## Start All Services

**Terminal 1 - Backend Server (start this first):**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Backend & Frontend Ngrok:**
```bash
ngrok start --all
```

**Terminal 3 - Frontend Server:**
```bash
cd frontend
npm run dev
```

## Testing
1. Visit https://guided-kite-heartily.ngrok-free.app to access the app
2. Test backend connectivity at https://9c99575b6efd.ngrok-free.app
3. Both should be working now with CORS properly configured

## Environment Behavior
- **Development**: `localhost:3000` → calls `localhost:8000`
- **Production**: `guided-kite-heartily.ngrok-free.app` → calls `9c99575b6efd.ngrok-free.app`

## Fixed Issues
- ✅ CORS now allows your ngrok frontend domain
- ✅ Backend URL updated in config
- ✅ ngrok.yml fixed (proto should be 'http', not a URL)