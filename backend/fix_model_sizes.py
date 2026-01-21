"""
Quick fix script to reduce .pkl file sizes by removing training artifacts.

This script:
1. Loads each trained model .pkl file
2. Removes _exercise_dates and split attributes from RT objects
3. Re-saves with the same data but much smaller file size

Run this to fix models that were trained before the cleanup fix.
"""

import sys
import pickle
import os

# Add parent directory to path for backend module imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import required classes so pickle can deserialize them
from backend.algorithms.rt import RT
from backend.models.rough_heston import RoughHeston
from backend.payoffs.game_payoffs import (
    UpAndOutCall,
    DownAndOutMinPut,
    DoubleBarrierMaxCall,
    StepBarrierCall,
    GameUpAndOutMinPut,
    DownAndOutBestOfKCall,
    DoubleBarrierLookbackFloatingPut,
    DoubleBarrierRankWeightedBasketCall,
    DoubleStepBarrierDispersionCall
)

# Data paths (SCRIPT_DIR already defined above for imports)
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
MODELS_DIR = os.path.join(DATA_DIR, 'trained_models')

def get_file_size_mb(filepath):
    """Get file size in MB."""
    return os.path.getsize(filepath) / (1024 ** 2)

def fix_model_file(model_path):
    """Load model, remove training artifacts, and re-save."""
    filename = os.path.basename(model_path)

    print(f"\nProcessing: {filename}")
    size_before = get_file_size_mb(model_path)
    print(f"  Size before: {size_before:.2f} MB")

    # Load the model
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    # Get RT object
    rt = model_data.get('rt')
    if rt is None:
        print(f"  ⚠️  No 'rt' key found, skipping")
        return

    # Remove training artifacts
    removed = []
    if hasattr(rt, '_exercise_dates'):
        delattr(rt, '_exercise_dates')
        removed.append('_exercise_dates')
    if hasattr(rt, 'split'):
        delattr(rt, 'split')
        removed.append('split')

    if not removed:
        print(f"  ✓ Already clean (no artifacts found)")
        return

    # Re-save the cleaned model
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)

    size_after = get_file_size_mb(model_path)
    reduction_pct = ((size_before - size_after) / size_before) * 100

    print(f"  Removed: {', '.join(removed)}")
    print(f"  Size after: {size_after:.2f} MB")
    print(f"  ✓ Saved {size_before - size_after:.2f} MB ({reduction_pct:.1f}% reduction)")

def main():
    """Fix all model files in the trained_models directory."""
    print("="*60)
    print("Model Size Fix Script")
    print("="*60)
    print(f"\nScanning directory: {MODELS_DIR}\n")

    # Find all .pkl files
    model_files = [
        os.path.join(MODELS_DIR, f)
        for f in os.listdir(MODELS_DIR)
        if f.endswith('.pkl')
    ]

    if not model_files:
        print("No .pkl files found!")
        return

    print(f"Found {len(model_files)} model files")

    total_before = 0
    total_after = 0

    for model_path in sorted(model_files):
        size_before = get_file_size_mb(model_path)
        total_before += size_before

        fix_model_file(model_path)

        size_after = get_file_size_mb(model_path)
        total_after += size_after

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total size before: {total_before:.2f} MB")
    print(f"Total size after:  {total_after:.2f} MB")
    print(f"Total saved:       {total_before - total_after:.2f} MB")
    print(f"Reduction:         {((total_before - total_after) / total_before) * 100:.1f}%")
    print("\n✓ All models fixed!")

if __name__ == '__main__':
    main()
