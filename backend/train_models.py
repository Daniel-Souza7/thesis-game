"""
Pre-training script for SRLSM models and path generation.

This script:
1. Generates training paths (50,000) for each product
2. Trains SRLSM models on these paths
3. Generates test paths (500) for in-game play
4. Saves models and paths to disk

Run this BEFORE starting the API server.
"""

import numpy as np
import pickle
import os
from backend.models.black_scholes import BlackScholes
from backend.payoffs.barrier_options import UpAndOutMinPut, DoubleKnockOutLookbackFloatingPut
from backend.algorithms.srlsm import SRLSM


# Game parameters from thesis
PARAMS = {
    'drift': 0.02,
    'volatility': 0.2,
    'spot': 100,
    'strike': 100,
    'dividend': 0,
    'maturity': 1,
    'nb_dates': 10,
    'hidden_size': 20,
    'factors': (1.0, 1.0, 1.0),
    'train_ITM_only': True,
    'use_payoff_as_input': False
}

# Training and test set sizes
NB_TRAIN_PATHS = 50000
NB_TEST_PATHS = 500

# Output directories
DATA_DIR = 'backend/data'
PATHS_DIR = os.path.join(DATA_DIR, 'paths')
MODELS_DIR = os.path.join(DATA_DIR, 'trained_models')


def train_upandout_minput():
    """Train SRLSM for UpAndOut Min Put (3 stocks, barrier=110)."""
    print("\n" + "="*60)
    print("Training UpAndOut Min Put (3 stocks)")
    print("="*60)

    # Create model (3 stocks)
    model = BlackScholes(
        drift=PARAMS['drift'],
        volatility=PARAMS['volatility'],
        spot=PARAMS['spot'],
        nb_stocks=3,  # 3 stocks
        nb_paths=NB_TRAIN_PATHS,
        nb_dates=PARAMS['nb_dates'],
        maturity=PARAMS['maturity'],
        dividend=PARAMS['dividend']
    )

    # Create payoff (barrier = 110)
    payoff = UpAndOutMinPut(strike=PARAMS['strike'], barrier=110)

    # Generate training paths
    print(f"\nGenerating {NB_TRAIN_PATHS} training paths...")
    train_paths, _ = model.generate_paths(seed=42)

    # Save training paths
    train_path_file = os.path.join(PATHS_DIR, 'upandout_train.npz')
    np.savez_compressed(train_path_file, paths=train_paths)
    print(f"Saved training paths to {train_path_file}")
    print(f"Shape: {train_paths.shape}")

    # Train SRLSM
    print("\nTraining SRLSM model...")
    srlsm = SRLSM(
        model=model,
        payoff=payoff,
        hidden_size=PARAMS['hidden_size'],
        factors=PARAMS['factors'],
        train_ITM_only=PARAMS['train_ITM_only'],
        use_payoff_as_input=PARAMS['use_payoff_as_input']
    )

    price, time_gen = srlsm.price(train_eval_split=2, stock_paths=train_paths)
    avg_exercise_time = srlsm.get_exercise_time()

    print(f"\nTraining complete!")
    print(f"  Option price: {price:.4f}")
    print(f"  Average exercise time: {avg_exercise_time:.4f}")

    # Save trained model
    model_file = os.path.join(MODELS_DIR, 'upandout_minput.pkl')
    with open(model_file, 'wb') as f:
        pickle.dump({
            'srlsm': srlsm,
            'model': model,
            'payoff': payoff,
            'price': price,
            'avg_exercise_time': avg_exercise_time
        }, f)
    print(f"Saved trained model to {model_file}")

    # Generate test paths
    print(f"\nGenerating {NB_TEST_PATHS} test paths...")
    model.nb_paths = NB_TEST_PATHS
    test_paths, _ = model.generate_paths(seed=123)

    test_path_file = os.path.join(PATHS_DIR, 'upandout_test.npz')
    np.savez_compressed(test_path_file, paths=test_paths)
    print(f"Saved test paths to {test_path_file}")
    print(f"Shape: {test_paths.shape}")

    return srlsm


def train_dko_lookback_put():
    """Train SRLSM for Double Knock-Out Lookback Put (1 stock, barriers=90/110)."""
    print("\n" + "="*60)
    print("Training Double Knock-Out Lookback Put (1 stock)")
    print("="*60)

    # Create model (1 stock)
    model = BlackScholes(
        drift=PARAMS['drift'],
        volatility=PARAMS['volatility'],
        spot=PARAMS['spot'],
        nb_stocks=1,  # 1 stock
        nb_paths=NB_TRAIN_PATHS,
        nb_dates=PARAMS['nb_dates'],
        maturity=PARAMS['maturity'],
        dividend=PARAMS['dividend']
    )

    # Create payoff (barriers = 90 and 110)
    payoff = DoubleKnockOutLookbackFloatingPut(
        strike=PARAMS['strike'],
        barrier_down=90,
        barrier_up=110
    )

    # Generate training paths
    print(f"\nGenerating {NB_TRAIN_PATHS} training paths...")
    train_paths, _ = model.generate_paths(seed=43)

    # Save training paths
    train_path_file = os.path.join(PATHS_DIR, 'dko_train.npz')
    np.savez_compressed(train_path_file, paths=train_paths)
    print(f"Saved training paths to {train_path_file}")
    print(f"Shape: {train_paths.shape}")

    # Train SRLSM
    print("\nTraining SRLSM model...")
    srlsm = SRLSM(
        model=model,
        payoff=payoff,
        hidden_size=PARAMS['hidden_size'],
        factors=PARAMS['factors'],
        train_ITM_only=PARAMS['train_ITM_only'],
        use_payoff_as_input=PARAMS['use_payoff_as_input']
    )

    price, time_gen = srlsm.price(train_eval_split=2, stock_paths=train_paths)
    avg_exercise_time = srlsm.get_exercise_time()

    print(f"\nTraining complete!")
    print(f"  Option price: {price:.4f}")
    print(f"  Average exercise time: {avg_exercise_time:.4f}")

    # Save trained model
    model_file = os.path.join(MODELS_DIR, 'dko_lookback_put.pkl')
    with open(model_file, 'wb') as f:
        pickle.dump({
            'srlsm': srlsm,
            'model': model,
            'payoff': payoff,
            'price': price,
            'avg_exercise_time': avg_exercise_time
        }, f)
    print(f"Saved trained model to {model_file}")

    # Generate test paths
    print(f"\nGenerating {NB_TEST_PATHS} test paths...")
    model.nb_paths = NB_TEST_PATHS
    test_paths, _ = model.generate_paths(seed=124)

    test_path_file = os.path.join(PATHS_DIR, 'dko_test.npz')
    np.savez_compressed(test_path_file, paths=test_paths)
    print(f"Saved test paths to {test_path_file}")
    print(f"Shape: {test_paths.shape}")

    return srlsm


def main():
    """Main training script."""
    print("\n" + "="*60)
    print("SRLSM Model Training Script")
    print("="*60)
    print(f"\nParameters:")
    for key, value in PARAMS.items():
        print(f"  {key}: {value}")
    print(f"\nTraining paths: {NB_TRAIN_PATHS}")
    print(f"Test paths: {NB_TEST_PATHS}")

    # Create output directories
    os.makedirs(PATHS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Train both models
    train_upandout_minput()
    train_dko_lookback_put()

    print("\n" + "="*60)
    print("All models trained successfully!")
    print("="*60)
    print(f"\nSaved to:")
    print(f"  Models: {MODELS_DIR}")
    print(f"  Paths: {PATHS_DIR}")
    print("\nYou can now start the API server.")


if __name__ == '__main__':
    main()
