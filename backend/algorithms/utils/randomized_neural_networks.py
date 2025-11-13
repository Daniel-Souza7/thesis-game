"""
Randomized neural networks for reservoir computing.

In randomized neural networks (reservoir computing):
- Hidden layer weights are randomly initialized and frozen
- Only the output layer is trained via least squares regression
- Much faster than training full neural networks
"""

import numpy as np
import torch


def init_weights(m, mean=0., std=1.):
    """
    Initialize linear layer weights with normal distribution.

    Args:
        m: PyTorch module
        mean: Mean of normal distribution
        std: Standard deviation of normal distribution
    """
    if isinstance(m, torch.nn.Linear):
        torch.nn.init.normal_(m.weight, mean, std)
        torch.nn.init.normal_(m.bias, mean, std)


def init_weights_gen(mean=0., std=1., mean_b=0., std_b=1., dist=0):
    """
    Generate weight initialization function with configurable distributions.

    Args:
        mean: Mean for weight distribution
        std: Std for weight distribution (or upper bound for uniform)
        mean_b: Mean for bias distribution
        std_b: Std for bias distribution (or upper bound for uniform)
        dist: Distribution type:
            0 - Normal distribution (default)
            1 - Uniform distribution
            2 - Xavier uniform initialization
            3 - Xavier normal initialization

    Returns:
        Initialization function that can be passed to model.apply()
    """
    def _init_weights(m):
        if isinstance(m, torch.nn.Linear):
            if dist == 0:
                # Normal distribution
                torch.nn.init.normal_(m.weight, mean, std)
                torch.nn.init.normal_(m.bias, mean_b, std_b)
            elif dist == 1:
                # Uniform distribution
                torch.nn.init.uniform_(m.weight, mean, std)
                torch.nn.init.uniform_(m.bias, mean_b, std_b)
            elif dist == 2:
                # Xavier uniform
                torch.nn.init.xavier_uniform_(m.weight)
                torch.nn.init.normal_(m.bias, mean_b, std_b)
            elif dist == 3:
                # Xavier normal
                torch.nn.init.xavier_normal_(m.weight)
                torch.nn.init.normal_(m.bias, mean_b, std_b)
            else:
                raise ValueError(
                    f"Invalid dist parameter: {dist}. Must be 0, 1, 2, or 3.\n"
                    f"  0: Normal, 1: Uniform, 2: Xavier Uniform, 3: Xavier Normal"
                )
    return _init_weights


class Reservoir2(torch.nn.Module):
    """
    PyTorch-based randomized neural network (reservoir).

    Architecture: Input → Linear(random) → Activation → Output

    The Linear layer weights are randomly initialized and frozen.
    Only used for feature extraction; actual regression happens externally.

    Args:
        hidden_size: Number of random features
        state_size: Dimension of input state
        factors: Tuple of scaling factors
            - If length 1: (input_scale,)
            - If length 8: (input_scale, ..., weight_init_params[5])
        activation: Activation function (default: LeakyReLU(0.5))
    """

    def __init__(self, hidden_size, state_size, factors=(1.,),
                 activation=torch.nn.LeakyReLU(0.5)):
        super().__init__()
        self.factors = factors
        self.hidden_size = hidden_size

        layers = [
            torch.nn.Linear(state_size, hidden_size, bias=True),
            activation
        ]
        self.NN = torch.nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialize random weights (then freeze them)."""
        if len(self.factors) == 8:
            # Extended initialization with custom parameters
            _init_weights = init_weights_gen(*self.factors[3:])
        else:
            # Default normal initialization
            _init_weights = init_weights

        self.apply(_init_weights)

        # Freeze all parameters - these are random features, not trainable
        for param in self.parameters():
            param.requires_grad = False

    def forward(self, input):
        """
        Extract random features from input.

        Args:
            input: Tensor of shape (batch_size, state_size)

        Returns:
            Random features of shape (batch_size, hidden_size)
        """
        # Scale input by first factor
        scaled_input = input * self.factors[0]
        return self.NN(scaled_input)
