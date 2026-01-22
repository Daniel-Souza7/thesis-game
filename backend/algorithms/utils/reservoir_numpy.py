"""
Numpy-only implementation of Reservoir2 for inference.

This module provides a pure numpy implementation of the Reservoir2 neural network,
enabling inference without PyTorch. This is critical for deployment on platforms
with size constraints (like Vercel's 250 MB limit) where PyTorch (1-2 GB) won't fit.

The weights are extracted from trained PyTorch models and stored as numpy arrays.
"""

import numpy as np
from scipy.special import erf as scipy_erf


def gelu(x):
    """GELU activation function (Gaussian Error Linear Unit).

    Uses the EXACT formula: GELU(x) = x * Φ(x) = x * 0.5 * (1 + erf(x / sqrt(2)))
    This matches PyTorch's GELU exactly, unlike the tanh approximation.

    Using the exact formula is critical because the model coefficients have
    magnitudes in the tens of thousands, so even tiny approximation errors
    compound into large prediction errors.
    """
    # Exact GELU using scipy's error function (matches PyTorch exactly)
    return x * 0.5 * (1 + scipy_erf(x / np.sqrt(2)))


def leaky_relu(x, negative_slope=0.5):
    """Leaky ReLU activation function."""
    return np.where(x > 0, x, negative_slope * x)


def relu(x):
    """ReLU activation function."""
    return np.maximum(0, x)


def tanh(x):
    """Tanh activation function."""
    return np.tanh(x)


def elu(x, alpha=1.0):
    """ELU activation function."""
    return np.where(x > 0, x, alpha * (np.exp(x) - 1))


def softplus(x, beta=1.0, threshold=20.0):
    """Softplus activation function."""
    return np.where(beta * x > threshold, x, np.log(1 + np.exp(beta * x)) / beta)


ACTIVATION_MAP = {
    'gelu': gelu,
    'leakyrelu': leaky_relu,
    'relu': relu,
    'tanh': tanh,
    'elu': elu,
    'softplus': softplus,
}


class Reservoir2Numpy:
    """
    Numpy-only implementation of Reservoir2 for inference.

    This class replicates the forward pass of PyTorch Reservoir2 using only numpy,
    eliminating the need for PyTorch at inference time.

    Args:
        weights: List of (weight, bias) tuples for each linear layer
        activation: Activation function name ('gelu', 'relu', 'tanh', etc.)
        factors: Tuple of scaling factors (first element scales input)
        dropout: Dropout probability (ignored during inference)
    """

    def __init__(self, weights, activation='gelu', factors=(1.,), dropout=0.0):
        """
        Initialize from extracted weights.

        Args:
            weights: List of (weight, bias) tuples, one per linear layer
            activation: String name of activation function
            factors: Scaling factors tuple
            dropout: Dropout probability (not used in inference)
        """
        self.weights = weights  # List of (weight, bias) tuples
        self.factors = factors
        self.dropout = dropout

        # Get activation function
        activation_lower = activation.lower() if isinstance(activation, str) else 'leakyrelu'
        self.activation_fn = ACTIVATION_MAP.get(activation_lower, leaky_relu)
        self.activation_name = activation_lower

    def __call__(self, x):
        """
        Forward pass using numpy only.

        Args:
            x: Input array of shape (batch_size, state_size)

        Returns:
            Output features of shape (batch_size, hidden_size)
        """
        # Scale input by first factor
        out = x * self.factors[0]

        # Forward through each layer: Linear -> Activation
        for i, (weight, bias) in enumerate(self.weights):
            # Linear: out = x @ W^T + b
            out = out @ weight.T + bias
            # Activation
            out = self.activation_fn(out)

        return out

    @classmethod
    def from_pytorch_reservoir(cls, pytorch_reservoir):
        """
        Create a Reservoir2Numpy from a PyTorch Reservoir2 module.

        Args:
            pytorch_reservoir: PyTorch Reservoir2 instance

        Returns:
            Reservoir2Numpy instance with extracted weights
        """
        weights = []

        # Extract weights from each Linear layer in the Sequential
        for module in pytorch_reservoir.NN:
            if hasattr(module, 'weight'):  # It's a Linear layer
                w = module.weight.detach().cpu().numpy().astype(np.float32)
                b = module.bias.detach().cpu().numpy().astype(np.float32)
                weights.append((w, b))

        # Determine activation name
        activation_name = 'leakyrelu'  # default
        for module in pytorch_reservoir.NN:
            module_name = module.__class__.__name__.lower()
            if 'gelu' in module_name:
                activation_name = 'gelu'
                break
            elif 'relu' in module_name and 'leaky' not in module_name:
                activation_name = 'relu'
                break
            elif 'tanh' in module_name:
                activation_name = 'tanh'
                break
            elif 'elu' in module_name and module_name != 'gelu':
                activation_name = 'elu'
                break
            elif 'leaky' in module_name:
                activation_name = 'leakyrelu'
                break
            elif 'softplus' in module_name:
                activation_name = 'softplus'
                break

        return cls(
            weights=weights,
            activation=activation_name,
            factors=pytorch_reservoir.factors,
            dropout=pytorch_reservoir.dropout
        )

    def to_dict(self):
        """Serialize to dictionary for pickle storage."""
        return {
            'weights': self.weights,
            'activation': self.activation_name,
            'factors': self.factors,
            'dropout': self.dropout,
        }

    @classmethod
    def from_dict(cls, data):
        """Create instance from dictionary."""
        return cls(
            weights=data['weights'],
            activation=data['activation'],
            factors=data['factors'],
            dropout=data.get('dropout', 0.0),
        )
