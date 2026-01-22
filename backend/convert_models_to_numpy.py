"""
Convert PyTorch RT models to numpy-only format for Vercel deployment.

This script converts trained RT models from PyTorch format to numpy-only format,
enabling deployment on size-constrained platforms like Vercel where PyTorch (1-2 GB)
cannot be installed.

Run this script locally (where you have PyTorch) before deploying:
    python backend/convert_models_to_numpy.py

The converted models will be saved as *_numpy.pkl files in the same directory.
"""

import os
import sys
import pickle

# Add parent directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import PyTorch (required for loading old models)
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
except ImportError:
    print("ERROR: PyTorch is required to run this conversion script.")
    print("Install it with: pip install torch")
    sys.exit(1)

import numpy as np
from backend.algorithms.utils.reservoir_numpy import Reservoir2Numpy


def convert_model_to_numpy(input_path, output_path=None):
    """
    Convert a PyTorch RT model to numpy-only format.

    Args:
        input_path: Path to the PyTorch pickle file
        output_path: Path for the output file (default: same name with _numpy suffix)

    Returns:
        bool: True if conversion succeeded
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = input_path  # Overwrite original file

    print(f"\nConverting: {os.path.basename(input_path)}")

    try:
        # Load the PyTorch model
        with open(input_path, 'rb') as f:
            model_data = pickle.load(f)

        # Get the RT object (could be 'rt' or 'srlsm' key)
        rt = model_data.get('rt', model_data.get('srlsm'))
        if rt is None:
            print(f"  ERROR: No 'rt' or 'srlsm' key found in model data")
            return False

        # Check if already converted
        if hasattr(rt, 'reservoir') and isinstance(rt.reservoir, dict):
            print(f"  SKIP: Model already appears to be in numpy format")
            return True

        # Convert the reservoir from PyTorch to numpy
        print(f"  - Converting reservoir (hidden_size={rt.hidden_size})")
        reservoir_numpy = Reservoir2Numpy.from_pytorch_reservoir(rt.reservoir)

        # Create numpy-compatible model data
        numpy_model_data = {
            'reservoir_data': reservoir_numpy.to_dict(),
            '_learned_coefficients': rt._learned_coefficients,
            'model': rt.model,
            'payoff': rt.payoff,
            'use_payoff_as_input': rt.use_payoff_as_input,
            'use_barrier_as_input': getattr(rt, 'use_barrier_as_input', False),
            'barrier_values': getattr(rt, 'barrier_values', []),
            'nb_base_fcts': rt.nb_base_fcts,
            'hidden_size': rt.hidden_size,
            'factors': rt.factors,
            'activation': getattr(rt, 'activation', 'gelu'),
        }

        # Create the new model_data dict with numpy rt
        new_model_data = {
            'rt': numpy_model_data,  # Store as dict instead of RT object
            'model': model_data['model'],
            'payoff': model_data['payoff'],
            'price': model_data['price'],
            'avg_exercise_time': model_data['avg_exercise_time'],
            '_is_numpy_format': True,  # Flag to indicate numpy format
        }

        # Save the converted model
        with open(output_path, 'wb') as f:
            pickle.dump(new_model_data, f)

        # Verify the new file size
        old_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        print(f"  - Original size: {old_size / 1024:.1f} KB")
        print(f"  - New size: {new_size / 1024:.1f} KB")
        print(f"  - Size change: {(new_size - old_size) / 1024:+.1f} KB")
        print(f"  ✓ Converted successfully")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_converted_model(model_path):
    """
    Verify that a converted model can be loaded without PyTorch.

    Args:
        model_path: Path to the converted pickle file

    Returns:
        bool: True if verification passed
    """
    print(f"\nVerifying: {os.path.basename(model_path)}")

    try:
        # Load the model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        # Check if it's in numpy format
        if not model_data.get('_is_numpy_format', False):
            print(f"  WARNING: Model not in numpy format")
            return False

        # Try to create RTNumpy from the data
        from backend.algorithms.rt_numpy import RTNumpy
        rt_numpy = RTNumpy(model_data['rt'])

        print(f"  ✓ Model loads correctly as RTNumpy")
        print(f"    - Coefficients for {len(rt_numpy._learned_coefficients)} time steps")
        print(f"    - Reservoir layers: {len(rt_numpy.reservoir.weights)}")

        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    """Convert all models in the trained_models directory."""
    models_dir = os.path.join(SCRIPT_DIR, 'data', 'trained_models')

    if not os.path.exists(models_dir):
        print(f"ERROR: Models directory not found: {models_dir}")
        return

    # Find all pickle files
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl') and not f.endswith('_numpy.pkl')]

    if not model_files:
        print(f"No model files found in {models_dir}")
        return

    print(f"Found {len(model_files)} model files to convert:")
    for f in model_files:
        print(f"  - {f}")

    # Convert each model
    success_count = 0
    for model_file in model_files:
        input_path = os.path.join(models_dir, model_file)
        if convert_model_to_numpy(input_path):
            success_count += 1

    print(f"\n{'='*50}")
    print(f"Conversion complete: {success_count}/{len(model_files)} models converted")

    # Verify all converted models
    print(f"\n{'='*50}")
    print("Verifying converted models...")

    verify_count = 0
    for model_file in model_files:
        model_path = os.path.join(models_dir, model_file)
        if verify_converted_model(model_path):
            verify_count += 1

    print(f"\n{'='*50}")
    print(f"Verification complete: {verify_count}/{len(model_files)} models verified")

    if verify_count == len(model_files):
        print("\n✓ All models converted and verified successfully!")
        print("\nNext steps:")
        print("1. Commit the converted models: git add backend/data/trained_models/*.pkl")
        print("2. Push to your branch: git push")
        print("3. Deploy to Vercel: vercel --prod")
    else:
        print("\n⚠ Some models failed conversion or verification. Check errors above.")


if __name__ == '__main__':
    main()
