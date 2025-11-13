"""
Verify that the project structure is correct (doesn't require dependencies).
"""

import os
import sys

print("Verifying project structure...\n")

required_files = [
    'backend/models/black_scholes.py',
    'backend/payoffs/barrier_options.py',
    'backend/algorithms/srlsm.py',
    'backend/algorithms/utils/randomized_neural_networks.py',
    'backend/train_models.py',
    'backend/api.py',
    'backend/requirements.txt',
    'frontend/package.json',
    'frontend/vite.config.js',
    'frontend/index.html',
    'frontend/src/main.jsx',
    'frontend/src/App.jsx',
    'frontend/src/components/GameBoard.jsx',
    'frontend/src/components/StockChart.jsx',
    'frontend/src/components/InfoPanel.jsx',
    'frontend/src/components/ControlPanel.jsx',
    'frontend/src/components/ResultsDisplay.jsx',
    'frontend/src/styles/index.css',
    'vercel.json',
    'README.md',
    'SETUP_INSTRUCTIONS.md',
    '.gitignore'
]

required_dirs = [
    'backend',
    'backend/models',
    'backend/payoffs',
    'backend/algorithms',
    'backend/algorithms/utils',
    'backend/data',
    'backend/data/trained_models',
    'backend/data/paths',
    'frontend',
    'frontend/src',
    'frontend/src/components',
    'frontend/src/styles'
]

all_ok = True

print("Checking directories...")
for directory in required_dirs:
    if os.path.isdir(directory):
        print(f"  ✓ {directory}")
    else:
        print(f"  ✗ {directory} - MISSING")
        all_ok = False

print("\nChecking files...")
for file_path in required_files:
    if os.path.isfile(file_path):
        print(f"  ✓ {file_path}")
    else:
        print(f"  ✗ {file_path} - MISSING")
        all_ok = False

print("\n" + "="*60)
if all_ok:
    print("Project structure is correct! ✓")
    print("="*60)
    print("\nNext steps:")
    print("1. Install backend dependencies:")
    print("   cd backend && pip install -r requirements.txt")
    print("\n2. Install frontend dependencies:")
    print("   cd frontend && npm install")
    print("\n3. Train the models:")
    print("   python backend/train_models.py")
    print("\n4. Start the backend:")
    print("   python backend/api.py")
    print("\n5. Start the frontend (in a new terminal):")
    print("   cd frontend && npm run dev")
    print("\nSee SETUP_INSTRUCTIONS.md for detailed instructions.")
else:
    print("Project structure has errors! ✗")
    print("="*60)
    sys.exit(1)
