"""
Generate test paths for model verification.

This script generates test paths using the EXACT same RoughHeston parameters
and seeding method that were used in train_models.py.

Usage:
    python backend/generate_test_paths.py

Output:
    backend/data/paths/test_1stock.npz
    backend/data/paths/test_3stock.npz
    backend/data/paths/test_7stock.npz
"""

import os
import sys
import numpy as np
import time

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.models.rough_heston import RoughHeston

# Model parameters - MUST match train_models.py PARAMS exactly
MODEL_PARAMS = {
    'drift': 0.02,
    'volatility': 0.29,
    'mean': 0.07,
    'speed': 0.5,
    'correlation': -0.75,
    'hurst': 0.03,
    'spot': 100,
    'dividend': 0,
    'maturity': 1,
    'nb_dates': 12,
    'v0': 0.026,
    'nb_steps_mult': 10,
}

# Test paths config - matches train_models.py TEST_PATHS_CONFIG
TEST_PATHS_CONFIG = {
    1: 500,
    3: 500,
    7: 500,
}

# Seeds - matches train_models.py (test seeds: 142, 143, 144)
TEST_SEEDS = {
    1: 142,
    3: 143,
    7: 144,
}


def generate_paths(nb_stocks):
    """Generate paths using RoughHeston model - matches train_models.py exactly."""
    nb_paths = TEST_PATHS_CONFIG[nb_stocks]
    seed = TEST_SEEDS[nb_stocks]

    print(f"\nGenerating {nb_paths:,} paths for {nb_stocks} stock(s) (seed={seed})...")

    # Create model - matches train_models.py generate_shared_paths()
    model = RoughHeston(
        drift=MODEL_PARAMS['drift'],
        volatility=MODEL_PARAMS['volatility'],
        mean=MODEL_PARAMS['mean'],
        speed=MODEL_PARAMS['speed'],
        correlation=MODEL_PARAMS['correlation'],
        hurst=MODEL_PARAMS['hurst'],
        spot=MODEL_PARAMS['spot'],
        nb_stocks=nb_stocks,
        nb_paths=nb_paths,
        nb_dates=MODEL_PARAMS['nb_dates'],
        maturity=MODEL_PARAMS['maturity'],
        dividend=MODEL_PARAMS['dividend'],
        v0=MODEL_PARAMS['v0'],
        nb_steps_mult=MODEL_PARAMS['nb_steps_mult'],
    )

    # Generate paths - pass seed to generate_paths() like train_models.py does
    t_start = time.time()
    paths, _ = model.generate_paths(seed=seed)
    gen_time = time.time() - t_start

    print(f"  Shape: {paths.shape}")
    print(f"  Dtype: {paths.dtype}")
    print(f"  Generation time: {gen_time:.1f}s")
    print(f"  Min: {paths.min():.2f}, Max: {paths.max():.2f}, Mean: {paths.mean():.2f}")

    return paths


def save_paths(paths, nb_stocks, output_dir):
    """Save paths to npz file."""
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'test_{nb_stocks}stock.npz')
    np.savez_compressed(output_path, paths=paths)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved to {output_path} ({size_kb:.1f} KB)")

    return output_path


def main():
    print("=" * 60)
    print("GENERATE TEST PATHS")
    print("(Matching train_models.py parameters exactly)")
    print("=" * 60)

    print("\nModel parameters (from train_models.py PARAMS):")
    for key, value in MODEL_PARAMS.items():
        print(f"  {key}: {value}")

    print("\nTest paths config (from train_models.py TEST_PATHS_CONFIG):")
    for nb_stocks, nb_paths in TEST_PATHS_CONFIG.items():
        print(f"  {nb_stocks}-stock: {nb_paths} paths (seed={TEST_SEEDS[nb_stocks]})")

    output_dir = os.path.join(SCRIPT_DIR, 'data', 'paths')

    for nb_stocks in [1, 3, 7]:
        paths = generate_paths(nb_stocks)
        save_paths(paths, nb_stocks, output_dir)

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nTest paths saved to: {output_dir}")
    print("\nNext steps:")
    print("1. Verify models: python backend/verify_models.py")
    print("2. If retraining: python backend/retrain_models.py")


if __name__ == '__main__':
    main()
