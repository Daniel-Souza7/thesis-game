"""
Retrain models using existing paths and save in RTNumpy-compatible format.

This script:
1. Loads pre-generated training paths (train_1stock.npz, etc.)
2. Trains RT models
3. Saves in format directly compatible with RTNumpy (no conversion needed)
4. Verifies inference matches training

Usage:
    python backend/retrain_models.py

Requirements:
    - PyTorch (for training)
    - Training paths in backend/data/paths/ (train_1stock.npz, train_3stock.npz, train_7stock.npz)
"""

import os
import sys
import pickle
import numpy as np
import time

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import PyTorch (required for training)
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
except ImportError:
    print("ERROR: PyTorch is required for training.")
    print("Install with: pip install torch")
    sys.exit(1)

from backend.algorithms.rt import RT
from backend.algorithms.rt_numpy import RTNumpy
from backend.algorithms.utils.reservoir_numpy import Reservoir2Numpy
from backend.models.rough_heston import RoughHeston

# Import all payoff classes
from backend.payoffs.game_payoffs import (
    UpAndOutCall,
    DownAndOutMinPut,
    DoubleBarrierMaxCall,
    StepBarrierCall as RandomlyMovingBarrierCall,
    GameUpAndOutMinPut as UpAndOutMinPut,
    DownAndOutBestOfKCall as DownAndOutBest2Call,
    DoubleBarrierLookbackFloatingPut,
    DoubleBarrierRankWeightedBasketCall,
    DoubleStepBarrierDispersionCall as DoubleMovingBarrierDispersionCall,
)

# Game configurations
GAME_CONFIGS = {
    'upandoutcall': {
        'payoff_class': UpAndOutCall,
        'payoff_args': {'strike': 100, 'barrier': 120},
        'nb_stocks': 1,
        'difficulty': 'Medium',
    },
    'downandoutminput': {
        'payoff_class': DownAndOutMinPut,
        'payoff_args': {'strike': 100, 'barrier': 85},
        'nb_stocks': 3,
        'difficulty': 'Medium',
    },
    'doublebarriermaxcall': {
        'payoff_class': DoubleBarrierMaxCall,
        'payoff_args': {'strike': 100, 'barrier_up': 130, 'barrier_down': 85},
        'nb_stocks': 7,
        'difficulty': 'Medium',
    },
    'randomlymovingbarriercall': {
        'payoff_class': RandomlyMovingBarrierCall,
        'payoff_args': {'strike': 100, 'initial_barrier': 125, 'seed': 42},
        'nb_stocks': 1,
        'difficulty': 'Hard',
    },
    'upandoutminput': {
        'payoff_class': UpAndOutMinPut,
        'payoff_args': {'strike': 100, 'barrier': 120},
        'nb_stocks': 3,
        'difficulty': 'Hard',
    },
    'downandoutbest2call': {
        'payoff_class': DownAndOutBest2Call,
        'payoff_args': {'strike': 100, 'barrier': 85, 'k': 2},
        'nb_stocks': 7,
        'difficulty': 'Hard',
    },
    'doublebarrierlookbackfloatingput': {
        'payoff_class': DoubleBarrierLookbackFloatingPut,
        'payoff_args': {'strike': 100, 'barrier_up': 115, 'barrier_down': 85},
        'nb_stocks': 1,
        'difficulty': 'Impossible',
    },
    'doublebarrierrankweightedbskcall': {
        'payoff_class': DoubleBarrierRankWeightedBasketCall,
        'payoff_args': {'strike': 100, 'barrier_up': 125, 'barrier_down': 80},
        'nb_stocks': 3,
        'difficulty': 'Impossible',
    },
    'doublemovingbarrierdispersioncall': {
        'payoff_class': DoubleMovingBarrierDispersionCall,
        'payoff_args': {'strike': 1, 'barrier_up': 115, 'barrier_down': 85, 'seed': 42},
        'nb_stocks': 7,
        'difficulty': 'Impossible',
    },
}

# Model parameters (RoughHeston)
MODEL_PARAMS = {
    'drift': 0.02,
    'volatility': 0.3,
    'spot': 100,
    'mean': 0.04,
    'speed': 2.0,
    'correlation': -0.7,
    'maturity': 1.0,
    'nb_dates': 12,
    'nb_paths': 15_000_000,
    'hurst': 0.25,
}

# RT training parameters
RT_PARAMS = {
    'hidden_size': 40,
    'factors': (1.0, 1.0, 1.0),
    'train_ITM_only': True,
    'use_payoff_as_input': True,
    'use_barrier_as_input': False,
    'activation': 'gelu',
    'dropout': 0.0,
}


def load_training_paths(nb_stocks):
    """Load pre-generated training paths."""
    paths_dir = os.path.join(SCRIPT_DIR, 'data', 'paths')
    path_file = os.path.join(paths_dir, f'train_{nb_stocks}stock.npz')

    if not os.path.exists(path_file):
        print(f"  ERROR: Training paths not found: {path_file}")
        print(f"  Please ensure train_{nb_stocks}stock.npz exists in backend/data/paths/")
        return None

    data = np.load(path_file)
    paths = data['paths']
    print(f"  Loaded {len(paths):,} training paths from {path_file}")
    return paths


def load_test_paths(nb_stocks):
    """Load test paths for verification."""
    paths_dir = os.path.join(SCRIPT_DIR, 'data', 'paths')
    path_file = os.path.join(paths_dir, f'test_{nb_stocks}stock.npz')

    if not os.path.exists(path_file):
        print(f"  Warning: Test paths not found: {path_file}")
        return None

    data = np.load(path_file)
    paths = data['paths']
    print(f"  Loaded {len(paths)} test paths from {path_file}")
    return paths


def convert_rt_to_numpy_format(rt):
    """Convert RT model to RTNumpy-compatible dict format."""
    # Extract numpy weights from PyTorch reservoir
    reservoir_numpy = Reservoir2Numpy.from_pytorch_reservoir(rt.reservoir)

    return {
        'reservoir_data': reservoir_numpy.to_dict(),
        '_learned_coefficients': rt._learned_coefficients,
        'model': rt.model,
        'payoff': rt.payoff,
        'use_payoff_as_input': rt.use_payoff_as_input,
        'use_barrier_as_input': rt.use_barrier_as_input,
        'barrier_values': rt.barrier_values,
        'nb_base_fcts': rt.nb_base_fcts,
        'hidden_size': rt.hidden_size,
        'factors': rt.factors,
        'activation': rt.activation,
    }


def train_game(game_name, config):
    """Train a single game model."""
    print(f"\n{'='*60}")
    print(f"Training: {game_name}")
    print(f"{'='*60}")

    # Load training paths
    paths = load_training_paths(config['nb_stocks'])
    if paths is None:
        return None

    # Create model
    model = RoughHeston(
        nb_stocks=config['nb_stocks'],
        **MODEL_PARAMS
    )

    # Create payoff
    payoff = config['payoff_class'](**config['payoff_args'])
    print(f"  Payoff: {payoff.__class__.__name__}")
    print(f"  Stocks: {config['nb_stocks']}")

    # Create RT and train
    rt = RT(model, payoff, **RT_PARAMS)

    print(f"  Training with {len(paths):,} paths...")
    t_start = time.time()
    price, time_path_gen = rt.price(train_eval_split=2, stock_paths=paths)
    train_time = time.time() - t_start

    avg_exercise_time = rt.get_exercise_time()

    print(f"  Price: {price:.4f}")
    print(f"  Avg exercise time: {avg_exercise_time:.4f}")
    print(f"  Training time: {train_time:.1f}s")

    # Convert to numpy format
    print(f"  Converting to numpy format...")
    rt_numpy_data = convert_rt_to_numpy_format(rt)

    # Create full model data
    model_data = {
        'rt': rt_numpy_data,
        'model': model,
        'payoff': payoff,
        'price': price,
        'avg_exercise_time': avg_exercise_time,
        '_is_numpy_format': True,
    }

    # Verify inference matches
    print(f"  Verifying inference...")
    rt_numpy = RTNumpy(rt_numpy_data)

    # Use same paths for verification (evaluation set)
    eval_paths = paths[len(paths)//2:][:1000]  # First 1000 of eval set

    # PyTorch inference
    exercise_dates_torch = rt.predict_exercise_decisions(eval_paths)
    avg_torch = np.mean(exercise_dates_torch / model.nb_dates)

    # Numpy inference
    exercise_dates_numpy = rt_numpy.predict_exercise_decisions(eval_paths)
    avg_numpy = np.mean(exercise_dates_numpy / model.nb_dates)

    # Compare
    match_rate = np.mean(exercise_dates_torch == exercise_dates_numpy)
    print(f"  PyTorch avg exercise time: {avg_torch:.4f}")
    print(f"  Numpy avg exercise time: {avg_numpy:.4f}")
    print(f"  Decision match rate: {match_rate*100:.1f}%")

    if match_rate < 0.95:
        print(f"  WARNING: Low match rate! There may be a bug.")

    return model_data


def save_model(game_name, model_data):
    """Save model to pickle file."""
    models_dir = os.path.join(SCRIPT_DIR, 'data', 'trained_models')
    os.makedirs(models_dir, exist_ok=True)

    output_path = os.path.join(models_dir, f'{game_name}.pkl')

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved to {output_path} ({size_kb:.1f} KB)")


def main():
    """Train all models."""
    print("="*60)
    print("RETRAIN MODELS WITH NUMPY-COMPATIBLE FORMAT")
    print("="*60)

    # Check for training paths
    paths_dir = os.path.join(SCRIPT_DIR, 'data', 'paths')
    required_stocks = set(c['nb_stocks'] for c in GAME_CONFIGS.values())

    print(f"\nChecking for training paths...")
    missing = []
    for nb_stocks in sorted(required_stocks):
        path_file = os.path.join(paths_dir, f'train_{nb_stocks}stock.npz')
        if os.path.exists(path_file):
            print(f"  ✓ train_{nb_stocks}stock.npz")
        else:
            print(f"  ✗ train_{nb_stocks}stock.npz (MISSING)")
            missing.append(nb_stocks)

    if missing:
        print(f"\nERROR: Missing training paths for {missing} stock(s).")
        print("Please ensure training paths are in backend/data/paths/")
        print("You may need to copy them from your local machine.")
        sys.exit(1)

    # Train each game
    success = 0
    failed = []

    for game_name, config in GAME_CONFIGS.items():
        try:
            model_data = train_game(game_name, config)
            if model_data is not None:
                save_model(game_name, model_data)
                success += 1
            else:
                failed.append(game_name)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed.append(game_name)

    # Summary
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {success}/{len(GAME_CONFIGS)}")
    if failed:
        print(f"Failed: {failed}")

    print("\nNext steps:")
    print("1. Verify models locally: python backend/verify_models.py")
    print("2. Commit changes: git add backend/data/trained_models/*.pkl")
    print("3. Push and deploy: git push && vercel --prod")


if __name__ == '__main__':
    main()
