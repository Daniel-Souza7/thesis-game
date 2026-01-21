"""
Algorithms for optimal stopping and option pricing.
"""

from backend.algorithms.rt import RT

# For backwards compatibility
SRLSM = RT

__all__ = ['RT', 'SRLSM']
