"""
Barrier option payoff functions.
"""

import numpy as np


class Payoff:
    """Base class for option payoff functions."""

    is_path_dependent = False  # Override in subclass if path-dependent

    def __init__(self, strike):
        """
        Initialize payoff with strike price.

        Args:
            strike: Strike price K
        """
        self.strike = strike

    def __call__(self, stock_paths):
        """
        Evaluate payoff for all paths at all timesteps.

        Args:
            stock_paths: Array of shape (nb_paths, nb_stocks, nb_dates+1)

        Returns:
            payoffs: Array of shape (nb_paths, nb_dates+1)
        """
        nb_paths, nb_stocks, nb_dates = stock_paths.shape
        payoffs = np.zeros((nb_paths, nb_dates), dtype=np.float32)

        for date in range(nb_dates):
            if self.is_path_dependent:
                # Pass full history up to this date
                payoffs[:, date] = self.eval(stock_paths[:, :, :date + 1])
            else:
                # Pass only current timestep
                payoffs[:, date] = self.eval(stock_paths[:, :, date])

        return payoffs

    def eval(self, X):
        """
        Evaluate payoff for given stock prices.

        Args:
            X: Array of shape (nb_paths, nb_stocks) or (nb_paths, nb_stocks, nb_dates+1)

        Returns:
            Array of shape (nb_paths,)
        """
        raise NotImplementedError("Subclasses must implement eval()")

    def __repr__(self):
        """String representation of payoff."""
        return f"{self.__class__.__name__}(strike={self.strike})"


class UpAndOutMinPut(Payoff):
    """
    Up-and-Out Put on Minimum of Multiple Stocks.

    Payoff: max(K - min(S_1(T), ..., S_d(T)), 0) if all stocks stay below barrier
    Otherwise: 0 (knocked out)

    For d=3 stocks, this pays the put option on the worst-performing stock,
    but only if none of the stocks breach the upper barrier.
    """

    is_path_dependent = True

    def __init__(self, strike, barrier=None):
        """
        Initialize Up-and-Out Min Put.

        Args:
            strike: Strike price K
            barrier: Upper barrier B_U (default: 1.2 * strike)
        """
        super().__init__(strike)
        self.barrier = barrier if barrier is not None else strike * 1.2

    def eval(self, X):
        """
        Evaluate Up-and-Out Min Put payoff.

        Args:
            X: Stock paths of shape (nb_paths, nb_stocks, nb_dates+1)

        Returns:
            Payoffs of shape (nb_paths,)
        """
        if X.ndim == 2:
            # Single timestep case
            terminal_min = np.min(X, axis=1)
            barrier_not_hit = np.max(X, axis=1) < self.barrier
            payoff = np.maximum(0, self.strike - terminal_min)
            return payoff * barrier_not_hit

        elif X.ndim == 3:
            # Full path case
            # Check if barrier was breached at any point
            max_along_path = np.max(X, axis=(1, 2))
            barrier_not_hit = max_along_path < self.barrier

            # Terminal payoff on minimum
            terminal_min = np.min(X[:, :, -1], axis=1)
            payoff = np.maximum(0, self.strike - terminal_min)

            return payoff * barrier_not_hit
        else:
            raise ValueError(f"Invalid dimensions: {X.ndim}")


class DoubleKnockOutLookbackFloatingPut(Payoff):
    """
    Double Knock-Out Lookback Floating Strike Put.

    Lookback put with floating strike: pays max(max_τ S(τ) - S(T), 0)
    (sell at historical maximum, buy at terminal price)

    Pays only if price stays BETWEEN both barriers throughout.

    For a basket: max(max_{τ,i} S_i(τ) - mean(S_1(T), ..., S_d(T)), 0)
    """

    is_path_dependent = True

    def __init__(self, strike, barrier_up=None, barrier_down=None):
        """
        Initialize Double Knock-Out Lookback Floating Put.

        Args:
            strike: Reference strike (for barrier defaults)
            barrier_up: Upper barrier (default: 1.1 * strike)
            barrier_down: Lower barrier (default: 0.9 * strike)
        """
        super().__init__(strike)
        self.barrier_up = barrier_up if barrier_up is not None else strike * 1.1
        self.barrier_down = barrier_down if barrier_down is not None else strike * 0.9

    def eval(self, X):
        """
        Evaluate Double Knock-Out Lookback Floating Put payoff.

        Args:
            X: Stock paths of shape (nb_paths, nb_stocks, nb_dates+1)

        Returns:
            Payoffs of shape (nb_paths,)
        """
        if X.ndim == 3:
            # Check if price stayed within barriers
            max_price = np.max(X, axis=(1, 2))
            min_price = np.min(X, axis=(1, 2))
            stays_in_range = (min_price > self.barrier_down) & (max_price < self.barrier_up)

            # Lookback floating strike: sell at maximum, buy at terminal
            if X.shape[1] > 1:
                # Multiple stocks: use basket average at terminal
                terminal_basket = np.mean(X[:, :, -1], axis=1)
            else:
                # Single stock
                terminal_basket = X[:, 0, -1]

            payoff = np.maximum(0, max_price - terminal_basket)

            return payoff * stays_in_range
        else:
            # Single timestep case
            max_price = np.max(X, axis=1)
            min_price = np.min(X, axis=1)
            stays_in_range = (min_price > self.barrier_down) & (max_price < self.barrier_up)

            if X.ndim == 2 and X.shape[1] > 1:
                terminal = np.mean(X, axis=1)
            else:
                terminal = X[:, -1] if X.ndim == 2 else X

            payoff = np.maximum(0, max_price - terminal)
            return payoff * stays_in_range
