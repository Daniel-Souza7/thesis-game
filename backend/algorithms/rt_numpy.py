"""
Numpy-only RT inference class.

This module provides inference-only functionality for RT models without requiring PyTorch.
The models must first be converted from PyTorch format using convert_models_to_numpy.py.

This enables deployment on size-constrained platforms like Vercel (250 MB limit)
where PyTorch (1-2 GB) cannot be installed.
"""

import numpy as np
import math
from backend.algorithms.utils.reservoir_numpy import Reservoir2Numpy


class RTNumpy:
    """
    Numpy-only RT inference class.

    This class can load and run inference on RT models that have been converted
    to numpy format (no PyTorch required).

    The model data should contain:
        - reservoir_data: Dict for Reservoir2Numpy.from_dict()
        - _learned_coefficients: Dict mapping time step to regression coefficients
        - model: The pricing model (for nb_stocks, nb_dates, etc.)
        - payoff: The payoff function
        - use_payoff_as_input: Whether payoff is used as input feature
        - use_barrier_as_input: Whether barrier values are used as input
        - barrier_values: List of barrier values (if use_barrier_as_input)
    """

    def __init__(self, model_data):
        """
        Initialize from converted model data.

        Args:
            model_data: Dictionary containing model parameters and numpy weights
        """
        # Load reservoir from numpy data
        self.reservoir = Reservoir2Numpy.from_dict(model_data['reservoir_data'])

        # Load learned coefficients
        self._learned_coefficients = model_data['_learned_coefficients']

        # Load model and payoff references
        self.model = model_data['model']
        self.payoff = model_data['payoff']

        # Configuration flags
        self.use_payoff_as_input = model_data.get('use_payoff_as_input', True)
        self.use_barrier_as_input = model_data.get('use_barrier_as_input', False)
        self.barrier_values = model_data.get('barrier_values', [])
        self.nb_barriers = len(self.barrier_values)

        # Detect if payoff is path-dependent
        self.is_path_dependent = getattr(self.payoff, 'is_path_dependent', False)

        # Number of basis functions
        self.nb_base_fcts = model_data.get('nb_base_fcts', len(self.reservoir.weights[-1][0]) + 1)

    def _eval_payoff(self, stock_paths, date=None):
        """
        Evaluate payoff at a specific date.

        Args:
            stock_paths: Full stock paths array (nb_paths, nb_stocks, nb_dates+1)
            date: Time index (if None, use full path for terminal payoff)

        Returns:
            payoffs: (nb_paths,) array of payoff values
        """
        if self.is_path_dependent:
            if date is None:
                return self.payoff.eval(stock_paths[:, :self.model.nb_stocks, :])
            else:
                return self.payoff.eval(stock_paths[:, :self.model.nb_stocks, :date + 1])
        else:
            if date is None:
                return self.payoff.eval(stock_paths[:, :self.model.nb_stocks, -1])
            else:
                return self.payoff.eval(stock_paths[:, :self.model.nb_stocks, date])

    def backward_induction_on_paths(self, stock_paths, var_paths=None):
        """
        Apply learned policy using backward induction.

        Args:
            stock_paths: (nb_paths, nb_stocks, nb_dates+1) - Stock price paths
            var_paths: (nb_paths, nb_stocks, nb_dates+1) - Variance paths (optional)

        Returns:
            exercise_times: (nb_paths,) - Time step when each path is exercised
            payoff_values: (nb_paths,) - Payoff value at exercise for each path
            price: float - Average discounted payoff
        """
        if not self._learned_coefficients:
            raise ValueError("No learned policy available.")

        nb_paths = stock_paths.shape[0]
        nb_dates = self.model.nb_dates

        # Get strike price for normalization
        if hasattr(self.payoff, 'strike'):
            strike = self.payoff.strike
        else:
            strike = self.model.spot if hasattr(self.model, 'spot') else stock_paths[0, :self.model.nb_stocks, 0]
        if np.isscalar(strike):
            strike = np.full(self.model.nb_stocks, strike, dtype=np.float32)

        # Compute all payoffs upfront
        payoffs = np.zeros((nb_paths, nb_dates + 1), dtype=np.float32)
        for t in range(nb_dates + 1):
            payoffs[:, t] = self._eval_payoff(stock_paths, date=t)

        # Initialize with terminal payoff
        values = payoffs[:, -1].copy()

        # Track exercise dates (initialize to maturity = nb_dates)
        exercise_dates = np.full(nb_paths, nb_dates, dtype=int)

        disc_factor = math.exp(-self.model.rate * self.model.maturity / nb_dates)

        # Backward induction from T-1 to 1
        for date in range(nb_dates - 1, 0, -1):
            if date not in self._learned_coefficients:
                continue

            # Current immediate exercise value
            immediate_exercise = payoffs[:, date]

            # Prepare state (normalize stock prices by strike)
            current_state = stock_paths[:, :self.model.nb_stocks, date] / strike

            if self.use_payoff_as_input:
                current_state = np.concatenate([current_state, payoffs[:, date:date+1]], axis=1)

            # Add barrier values as input hint (if enabled)
            if self.nb_barriers > 0:
                strike_scalar = strike[0] if isinstance(strike, np.ndarray) else strike
                barrier_features = np.array([[b / strike_scalar for b in self.barrier_values]], dtype=np.float32)
                barrier_features = np.repeat(barrier_features, current_state.shape[0], axis=0)
                current_state = np.concatenate([current_state, barrier_features], axis=1)

            # Get learned coefficients for this time step
            coefficients = self._learned_coefficients[date]

            # Evaluate basis functions using numpy reservoir
            basis = self.reservoir(current_state.astype(np.float32))
            basis = np.concatenate([basis, np.ones((len(basis), 1), dtype=np.float32)], axis=1)

            # Compute continuation values
            continuation_values = np.dot(basis, coefficients)
            continuation_values = np.maximum(0, continuation_values)

            # Discount future values
            discounted_values = values * disc_factor

            # Exercise decision
            exercise_now = immediate_exercise > continuation_values

            # Update values
            values = np.where(exercise_now, immediate_exercise, discounted_values)

            # Track exercise dates
            exercise_dates[exercise_now] = date

        # Final discount to time 0
        discounted_continuation = values * disc_factor
        payoff_0 = self._eval_payoff(stock_paths, date=0)
        final_values = np.maximum(payoff_0, discounted_continuation)

        # Extract payoff values at exercise time
        payoff_values = np.array([payoffs[i, exercise_dates[i]] for i in range(nb_paths)])

        price = np.mean(final_values)

        return exercise_dates, payoff_values, price

    def predict_exercise_decisions(self, test_paths):
        """
        Predict exercise decisions for test paths.

        Args:
            test_paths: Stock paths of shape (nb_paths, nb_stocks, nb_dates+1)

        Returns:
            exercise_dates: Array of shape (nb_paths,) with exercise date for each path
        """
        exercise_dates, _, _ = self.backward_induction_on_paths(test_paths)
        return exercise_dates


def convert_rt_to_numpy(rt_pytorch):
    """
    Convert a PyTorch RT model to numpy-only format.

    Args:
        rt_pytorch: PyTorch RT instance with trained model

    Returns:
        dict: Model data that can be used with RTNumpy
    """
    from backend.algorithms.utils.reservoir_numpy import Reservoir2Numpy

    return {
        'reservoir_data': Reservoir2Numpy.from_pytorch_reservoir(rt_pytorch.reservoir).to_dict(),
        '_learned_coefficients': rt_pytorch._learned_coefficients,
        'model': rt_pytorch.model,
        'payoff': rt_pytorch.payoff,
        'use_payoff_as_input': rt_pytorch.use_payoff_as_input,
        'use_barrier_as_input': rt_pytorch.use_barrier_as_input,
        'barrier_values': rt_pytorch.barrier_values,
        'nb_base_fcts': rt_pytorch.nb_base_fcts,
    }
