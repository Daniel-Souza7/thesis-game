# Deployment Guide

## Architecture

- **Backend**: Python/Flask API deployed on Render (Free tier - 512MB RAM)
- **Frontend**: React/Vite app deployed on Vercel
- **Strategy**: Lazy loading with 1 model cached at a time

## Backend (Render)

### Memory Optimization
The app uses **lazy loading** to fit all 9 games in 512MB:
- Only 1 model loaded in memory at a time (max 85MB)
- Models load on-demand when requested
- Default game pre-loaded at startup for instant first click
- Total memory usage: ~300-400MB (safe margin)

### Avoiding Cold Starts

Render's free tier spins down after **15 minutes** of inactivity. To prevent this:

1. **Use a free cron service** to ping the keep-alive endpoint every 14 minutes:
   - Endpoint: `https://thesis-game-backend-gzpt.onrender.com/api/keepalive`
   - Recommended services:
     - [cron-job.org](https://cron-job.org) - Free, reliable
     - [UptimeRobot](https://uptimerobot.com) - Free monitoring with pings
     - [EasyCron](https://www.easycron.com) - Free tier available

2. **Setup instructions for cron-job.org**:
   ```
   1. Sign up at https://cron-job.org
   2. Create new cron job
   3. URL: https://thesis-game-backend-gzpt.onrender.com/api/keepalive
   4. Interval: Every 14 minutes
   5. Save and enable
   ```

### Endpoints

- `GET /api/health` - Health check
- `GET /api/keepalive` - Keep-alive (for cron jobs)
- `GET /api/game/info` - List all available games
- `GET /api/game/start?product={game_id}` - Start a new game

## Frontend (Vercel)

### Environment Variables

Production environment is configured in `frontend/.env.production`:
```
VITE_API_BASE_URL=https://thesis-game-backend-gzpt.onrender.com/api
```

### Deployment
1. Push to GitHub
2. Vercel auto-deploys from the `claude/thesis-game-minigame-app-*` branch
3. Frontend available at your Vercel URL

## Available Games

All 9 games are available with lazy loading:

**MEDIUM:**
- UpAndOutCall (1 stock, 13MB)
- DownAndOutMinPut (3 stocks, 37MB)
- DoubleBarrierMaxCall (7 stocks, 85MB)

**HARD:**
- RandomlyMovingBarrierCall (1 stock, 13MB)
- UpAndOutMinPut (3 stocks, 37MB)
- DownAndOutBest2Call (7 stocks, 85MB)

**IMPOSSIBLE:**
- DoubleBarrierLookbackFloatingPut (1 stock, 13MB)
- DoubleBarrierRankWeightedBskCall (3 stocks, 37MB)
- DoubleMovingBarrierDispersionCall (7 stocks, 85MB)

## Performance Notes

- **First game click**: Instant (pre-loaded at startup)
- **Switching games**: 3-5 seconds (loading new model)
- **Cold start** (if service spun down): 10-15 seconds
  - Avoided with keep-alive cron job

## Upgrading for Better Performance

To remove lazy loading delays and cold starts:

**Render Starter Plan ($7/month)**:
- 2GB RAM → Can load all models at startup
- No cold starts
- Instant game switching
