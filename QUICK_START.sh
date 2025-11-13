#!/bin/bash

# Quick start script for Optimal Stopping Game

echo "=================================="
echo "Optimal Stopping Game - Quick Start"
echo "=================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo "✅ Node.js found: $(node --version)"
echo ""

# Step 1: Install backend dependencies
echo "Step 1: Installing backend dependencies..."
cd backend
pip3 install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi
echo "✅ Backend dependencies installed"
cd ..

# Step 2: Install frontend dependencies
echo ""
echo "Step 2: Installing frontend dependencies..."
cd frontend
npm install --silent
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi
echo "✅ Frontend dependencies installed"
cd ..

# Step 3: Train models
echo ""
echo "Step 3: Training SRLSM models (this will take 2-5 minutes)..."
echo "Generating 50,000 training paths and training models..."
python3 backend/train_models.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to train models"
    exit 1
fi
echo "✅ Models trained successfully"

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo "=================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend server:"
echo "   python3 backend/api.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Enjoy the game!"
