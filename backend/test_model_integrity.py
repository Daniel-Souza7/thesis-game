"""
Test if cleaned models still have the necessary data for predictions.
"""

import sys
import os
import pickle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.algorithms.rt import RT
from backend.models.rough_heston import RoughHeston
from backend.payoffs.game_payoffs import *

MODELS_DIR = os.path.join(SCRIPT_DIR, 'data', 'trained_models')

def test_model(model_path):
    """Test if a model file has the required data."""
    filename = os.path.basename(model_path)
    print(f"\nTesting: {filename}")

    try:
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        rt = model_data.get('rt')
        if rt is None:
            print(f"  ❌ No RT object found")
            return False

        # Check for learned coefficients
        if not hasattr(rt, '_learned_coefficients'):
            print(f"  ❌ Missing _learned_coefficients")
            return False

        if not rt._learned_coefficients:
            print(f"  ❌ _learned_coefficients is empty!")
            return False

        # Check for reservoir
        if not hasattr(rt, 'reservoir'):
            print(f"  ❌ Missing reservoir")
            return False

        print(f"  ✓ Has _learned_coefficients: {len(rt._learned_coefficients)} time steps")
        print(f"  ✓ Has reservoir: {type(rt.reservoir).__name__}")

        # Check model data
        if 'price' in model_data:
            print(f"  ✓ Price: {model_data['price']:.4f}")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("Model Integrity Test")
    print("="*60)

    model_files = [
        os.path.join(MODELS_DIR, f)
        for f in os.listdir(MODELS_DIR)
        if f.endswith('.pkl')
    ]

    working = 0
    broken = 0

    for model_path in sorted(model_files):
        if test_model(model_path):
            working += 1
        else:
            broken += 1

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Working models: {working}")
    print(f"Broken models: {broken}")

    if broken > 0:
        print("\n⚠️  MODELS ARE BROKEN - DO NOT USE THESE FILES!")
        print("Restore from backup and use a corrected cleanup script.")

if __name__ == '__main__':
    main()
