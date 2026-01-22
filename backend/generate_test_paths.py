"""
Generate test paths for model verification.

This script generates test paths using the same RoughHeston parameters
that were used to generate training paths, ensuring consistency.

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

# Model parameters - MUST match training paths exactly
MODEL_PARAMS = {
    'drift': 0.02,
    'volatility': 0.29,
    'spot': 100,
    'mean': 0.07,
    'speed': 0.5,
    'correlation': -0.75,
    'maturity': 1.0,
    'nb_dates': 12,
    'hurst': 0.03,
    'dividend': 0,
    'v0': 0.026,
    'nb_steps_mult': 10,
}

# Number of test paths to generate (much smaller than training)
NB_TEST_PATHS = 10_000

# Stock configurations needed
STOCK_CONFIGS = [1, 3, 7]


def generate_paths(nb_stocks, nb_paths, seed=12345):
    """Generate paths using RoughHeston model."""
    print(f"\nGenerating {nb_paths:,} paths for {nb_stocks} stock(s)...")

    # Set seed for reproducibility
    np.random.seed(seed + nb_stocks)

    # Create model
    model = RoughHeston(
        nb_stocks=nb_stocks,
        nb_paths=nb_paths,
        **MODEL_PARAMS
    )

    # Generate paths
    t_start = time.time()
    paths = model.generate_paths()
    gen_time = time.time() - t_start

    print(f"  Shape: {paths.shape}")
    print(f"  Generation time: {gen_time:.1f}s")
    print(f"  Min: {paths.min():.2f}, Max: {paths.max():.2f}, Mean: {paths.mean():.2f}")

    return paths


def save_paths(paths, nb_stocks, output_dir):
    """Save paths to npz file."""
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'test_{nb_stocks}stock.npz')
    np.savez_compressed(output_path, paths=paths)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved to {output_path} ({size_mb:.1f} MB)")

    return output_path


def main():
    print("=" * 60)
    print("GENERATE TEST PATHS")
    print("=" * 60)

    print("\nModel parameters:")
    for key, value in MODEL_PARAMS.items():
        print(f"  {key}: {value}")

    print(f"\nNumber of test paths: {NB_TEST_PATHS:,}")

    output_dir = os.path.join(SCRIPT_DIR, 'data', 'paths')

    for nb_stocks in STOCK_CONFIGS:
        paths = generate_paths(nb_stocks, NB_TEST_PATHS)
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
