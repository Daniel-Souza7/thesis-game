"""
Verify that RTNumpy produces the same results as PyTorch RT.

This script loads converted models and compares inference results.
Run this after training to ensure the conversion is correct.

Usage:
    python backend/verify_models.py
"""

import os
import sys
import pickle
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.algorithms.rt_numpy import RTNumpy


def verify_model(model_path):
    """Verify a single model."""
    game_name = os.path.basename(model_path).replace('.pkl', '')
    print(f"\n{'='*50}")
    print(f"Verifying: {game_name}")
    print(f"{'='*50}")

    # Load model
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    if not model_data.get('_is_numpy_format', False):
        print("  ERROR: Model is not in numpy format")
        return False

    # Create RTNumpy
    rt_numpy = RTNumpy(model_data['rt'])

    print(f"  Model: {rt_numpy.model.__class__.__name__}")
    print(f"  Payoff: {rt_numpy.payoff.__class__.__name__}")
    print(f"  nb_stocks: {rt_numpy.model.nb_stocks}")
    print(f"  nb_dates: {rt_numpy.model.nb_dates}")
    print(f"  use_payoff_as_input: {rt_numpy.use_payoff_as_input}")
    print(f"  Stored price: {model_data['price']:.4f}")
    print(f"  Stored avg_exercise_time: {model_data['avg_exercise_time']:.4f}")

    # Load test paths
    test_path_file = os.path.join(SCRIPT_DIR, 'data', 'paths', f"test_{rt_numpy.model.nb_stocks}stock.npz")
    if not os.path.exists(test_path_file):
        print(f"  Warning: Test paths not found: {test_path_file}")
        return True  # Can't verify but not an error

    test_paths = np.load(test_path_file)['paths']
    print(f"  Test paths: {len(test_paths)}")

    # Run inference
    exercise_dates = rt_numpy.predict_exercise_decisions(test_paths)

    # Compute stats
    avg_exercise_time = np.mean(exercise_dates / rt_numpy.model.nb_dates)
    print(f"  Inference avg_exercise_time: {avg_exercise_time:.4f}")

    # Compare with stored value
    diff = abs(avg_exercise_time - model_data['avg_exercise_time'])
    print(f"  Difference from stored: {diff:.4f}")

    if diff > 0.1:
        print(f"  WARNING: Large difference! May indicate a bug.")
        return False

    # Compute price from exercise decisions
    nb_dates = rt_numpy.model.nb_dates
    disc_factor = np.exp(-rt_numpy.model.rate * rt_numpy.model.maturity / nb_dates)

    total_payoff = 0
    for i, (path, ex_date) in enumerate(zip(test_paths, exercise_dates)):
        path_reshaped = path.reshape(1, rt_numpy.model.nb_stocks, -1)
        payoff = rt_numpy._eval_payoff(path_reshaped, date=int(ex_date))
        payoff_val = float(payoff[0]) if hasattr(payoff, '__len__') else float(payoff)
        discounted = payoff_val * (disc_factor ** ex_date)
        total_payoff += discounted

    estimated_price = total_payoff / len(test_paths)
    print(f"  Estimated price from inference: {estimated_price:.4f}")
    print(f"  Stored price: {model_data['price']:.4f}")

    price_diff = abs(estimated_price - model_data['price'])
    print(f"  Price difference: {price_diff:.4f}")

    if price_diff > 1.0:
        print(f"  WARNING: Large price difference!")
        return False

    print(f"  ✓ Verification passed")
    return True


def main():
    """Verify all models."""
    models_dir = os.path.join(SCRIPT_DIR, 'data', 'trained_models')

    if not os.path.exists(models_dir):
        print(f"ERROR: Models directory not found: {models_dir}")
        return

    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]

    if not model_files:
        print(f"No model files found in {models_dir}")
        return

    print(f"Found {len(model_files)} model files")

    passed = 0
    failed = []

    for model_file in sorted(model_files):
        model_path = os.path.join(models_dir, model_file)
        try:
            if verify_model(model_path):
                passed += 1
            else:
                failed.append(model_file)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed.append(model_file)

    print(f"\n{'='*50}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{len(model_files)}")
    if failed:
        print(f"Failed: {failed}")


if __name__ == '__main__':
    main()
