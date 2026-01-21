# Vercel Deployment Guide - Unified Stack

## Architecture (Updated)

**Everything on Vercel:**
- ✅ Frontend: React/Vite → Vercel CDN
- ✅ Backend: Flask API → Vercel Serverless Functions
- ✅ Data: Test paths + models (~320 KB) → Bundled in deployment

**Key Benefits:**
- No separate backend hosting needed
- Data bundled = faster cold starts (~2-4s vs 10-15s)
- Simpler deployment (one platform)
- Better free tier limits

## Deployment Steps

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Deploy

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

## What Gets Deployed

### ✅ Included (~320 KB):
```
├── api/index.py           (Serverless function wrapper)
├── backend/
│   ├── data/
│   │   ├── paths/
│   │   │   ├── test_1stock.npz   (~21 KB)
│   │   │   ├── test_3stock.npz   (~62 KB)
│   │   │   └── test_7stock.npz   (~144 KB)
│   │   └── trained_models/
│   │       └── *.pkl (9 models,  ~90 KB total)
│   ├── algorithms/
│   ├── models/
│   ├── payoffs/
│   └── api.py
└── frontend/
```

### ❌ Excluded (via .vercelignore):
- `train_*.npz` files (~546 MB training data)
- Training scripts
- Python cache
- Documentation

## Configuration Files

### `vercel.json`
```json
{
  "version": 2,
  "builds": [
    { "src": "frontend/package.json", "use": "@vercel/static-build" },
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/index.py" },
    { "src": "/(.*)", "dest": "/frontend/$1" }
  ],
  "functions": {
    "api/index.py": {
      "memory": 1024,
      "maxDuration": 10
    }
  }
}
```

## API Endpoints

After deployment:

```
https://your-project.vercel.app/api/game/start?product=upandoutcall
https://your-project.vercel.app/api/game/info
```

## Performance

### Cold Start (after ~5 min idle):
- **Time**: ~2-4 seconds
- **Process**:
  1. Spin up Python environment
  2. Load Flask + dependencies
  3. Load model from disk (~10 KB)
  4. Return response

### Warm Request:
- **Time**: ~200-500ms
- Model already in memory

## Model File Sizes (After Cleanup)

All 9 models total: **~90 KB**
- 1-stock games: ~10 KB each
- 3-stock games: ~10 KB each
- 7-stock games: ~10 KB each

Training artifacts removed:
- ~~Before: 503 MB~~
- **After: 90 KB** (99.98% reduction!)

## Free Tier Limits

**Vercel Free:**
- Bandwidth: 100 GB/month
- Serverless executions: 100 GB-Hours/month
- Functions: 10s max duration

**Estimated capacity:**
- ~100,000+ game requests/month

## Troubleshooting

### Backend 404 Errors
Frontend must call `/api/*` routes:
```javascript
axios.get('/api/game/start?product=upandoutcall')
```

### Cold Start Timeout
Increase duration in `vercel.json`:
```json
"maxDuration": 30
```

### Out of Memory
Increase memory (max 3008 MB):
```json
"memory": 3008
```

## Update Models

1. Train locally: `python backend/train_models.py`
2. Commit `.pkl` files
3. Deploy: `vercel --prod`

## Alternative Deployment Options

### Option A: Vercel (Current - Recommended)
- ✅ Everything bundled
- ✅ Fast cold starts
- ✅ Simple deployment

### Option B: Separate Backend (Previous Setup)
- Backend: Railway/Render/Fly.io
- Frontend: Vercel
- Need keep-alive pings
- Slower cold starts

## Cost Comparison

| Platform | Cost | Cold Start | Notes |
|----------|------|------------|-------|
| **Vercel (unified)** | Free | 2-4s | Bundled data, simple |
| Render + Vercel | Free | 10-15s | Needs keep-alive |
| Railway + Vercel | $5/mo | < 1s | Always on |

## Production Checklist

- [ ] Deploy to Vercel: `vercel --prod`
- [ ] Test all 9 games
- [ ] Verify cold start < 10s
- [ ] Check API routes work
- [ ] Set custom domain (optional)
- [ ] Delete training files locally

## Support

- Vercel Docs: https://vercel.com/docs
- Python Runtime: https://vercel.com/docs/functions/serverless-functions/runtimes/python
