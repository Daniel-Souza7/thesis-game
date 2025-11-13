# Optimal Stopping Game

An interactive web game where players challenge machine learning algorithms (SRLSM) on optimal stopping problems for financial derivatives with early exercise features.

## Overview

This application lets users "battle" against trained SRLSM (Special Randomized Least Squares Monte Carlo) algorithms in an optimal stopping game. Players make real-time decisions to either hold or exercise barrier options, competing to achieve higher payoffs than the machine.

## Features

- **Two Game Modes:**
  - **Up-and-Out Min Put**: 3-stock option with upper barrier at 110
  - **Double Knock-Out Lookback Put**: 1-stock lookback option with barriers at 90 and 110

- **Interactive Gameplay:**
  - Real-time stock price path animation
  - Step-by-step decision making (Hold vs Exercise)
  - Live comparison with machine decisions
  - Retro arcade game aesthetic

- **Pre-trained Models:**
  - SRLSM algorithms trained on 50,000 paths
  - 500 pre-generated test paths for smooth gameplay
  - Instant game start (no training delay)

## Project Structure

```
thesis-game/
├── backend/                  # Python backend
│   ├── models/              # Black-Scholes path generator
│   ├── payoffs/             # Barrier option payoff functions
│   ├── algorithms/          # SRLSM implementation
│   ├── data/                # Pre-trained models and paths
│   ├── train_models.py      # Training script
│   ├── api.py               # Flask API server
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── styles/          # CSS styling
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── vercel.json              # Deployment config
└── README.md
```

## Installation & Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- pip and npm

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Train the models (REQUIRED - do this before running the app):**
   ```bash
   python train_models.py
   ```

   This will:
   - Generate 50,000 training paths for each game
   - Train SRLSM models
   - Generate 500 test paths
   - Save everything to `backend/data/`

   Expected output:
   ```
   Training paths: 50000
   Test paths: 500

   Training UpAndOut Min Put (3 stocks)...
   Training DKO Lookback Put (1 stock)...

   All models trained successfully!
   ```

3. **Start the API server:**
   ```bash
   python api.py
   ```

   Server runs on `http://localhost:5000`

### Frontend Setup

1. **Install Node dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

   App runs on `http://localhost:3000`

3. **Build for production:**
   ```bash
   npm run build
   ```

## Game Parameters

Based on thesis research with the following parameters:

| Parameter | Value |
|-----------|-------|
| Drift (r) | 0.02 |
| Volatility (σ) | 0.2 |
| Initial Spot | 100 |
| Strike (K) | 100 |
| Dividend (q) | 0 |
| Maturity (T) | 1 year |
| Time Steps | 10 |
| Hidden Size | 20 neurons |
| Factors | (1.0, 1.0, 1.0) |

### Game 1: Up-and-Out Min Put
- **Stocks**: 3
- **Payoff**: max(K - min(S₁, S₂, S₃), 0)
- **Barrier**: 110 (upper)
- **Rule**: Option knocked out if any stock hits 110

### Game 2: Double Knock-Out Lookback Put
- **Stocks**: 1
- **Payoff**: max(max_τ S(τ) - S(T), 0)
- **Barriers**: 90 (lower), 110 (upper)
- **Rule**: Option knocked out if stock hits either barrier

## How to Play

1. **Game loads** with Up-and-Out Min Put by default
2. **Watch** stock prices animate step-by-step
3. **Decide** at each time step:
   - Click **HOLD** to continue to next step
   - Click **EXERCISE** to lock in current payoff
4. **Compete** against the machine's optimal strategy
5. **Win** by achieving a higher payoff than the algorithm!

### Game Flow

- **If you exercise first**: Your payoff is locked, then a fast animation shows the machine's remaining decisions
- **If machine exercises first**: Machine's payoff is locked, you can continue playing
- **If barrier is hit**: Game ends immediately, payoff becomes 0, machine's path is revealed
- **At maturity**: Option automatically exercises if not done earlier

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/game/info` - Get game parameters
- `GET /api/game/start?product={upandout|dko}` - Start new game

## Deployment

### Vercel Deployment

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Important**: Make sure to run `train_models.py` locally first and commit the trained models to git, as Vercel has limited build time for training.

Alternatively, deploy via Vercel dashboard by connecting your GitHub repository.

## Technical Details

### SRLSM Algorithm

The Special Randomized Least Squares Monte Carlo (SRLSM) algorithm:
- Handles path-dependent options (barriers, lookbacks)
- Uses randomized neural networks for continuation value estimation
- Backward induction from maturity to present
- Optimal stopping strategy learned from training paths

### Stock Model

Geometric Brownian Motion (GBM):
```
dS_t = (r - q) S_t dt + σ S_t dW_t
```

### Tech Stack

- **Backend**: Python, Flask, PyTorch, NumPy
- **Frontend**: React, Vite, Recharts
- **Styling**: Retro arcade CSS (pixel fonts, neon colors, CRT effects)
- **Deployment**: Vercel

## Troubleshooting

### "Failed to start game"
- Ensure backend server is running on port 5000
- Check that models are trained (run `train_models.py`)
- Verify `backend/data/` contains `.pkl` and `.npz` files

### "Module not found" errors
- Backend: `pip install -r requirements.txt`
- Frontend: `npm install`

### Training takes too long
- Training 50k paths should take 2-5 minutes
- Reduce `NB_TRAIN_PATHS` in `train_models.py` for testing (min 1000)

## License

This project is part of a thesis on optimal stopping problems for financial derivatives.

## Author

Created for thesis research on pricing financial derivatives with early exercise features using reinforcement learning and Monte Carlo methods.
