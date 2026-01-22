"""
Algorithms for optimal stopping and option pricing.
"""

# Always import numpy-only inference class (no PyTorch needed)
from backend.algorithms.rt_numpy import RTNumpy

# Try to import PyTorch RT class (only available when torch is installed)
try:
    from backend.algorithms.rt import RT
    # For backwards compatibility
    SRLSM = RT
    __all__ = ['RT', 'RTNumpy', 'SRLSM']
except ImportError:
    # PyTorch not available - only numpy inference is available
    RT = None
    SRLSM = None
    __all__ = ['RTNumpy']
