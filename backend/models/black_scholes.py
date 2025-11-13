"""
Black-Scholes model for generating stock price paths.
"""

import math
import numpy as np


class BlackScholes:
    """
    Geometric Brownian Motion (GBM) stock price model.

    dS_t = (drift - dividend) * S_t * dt + volatility * S_t * dW_t
    """

    def __init__(self, drift, volatility, nb_paths, nb_stocks, nb_dates,
                 spot, maturity, dividend=0, **kwargs):
        """
        Initialize Black-Scholes model.

        Args:
            drift: Risk-free rate (r)
            volatility: Volatility (sigma)
            nb_paths: Number of paths to generate
            nb_stocks: Number of stocks (dimension d)
            nb_dates: Number of time steps
            spot: Initial stock price S_0
            maturity: Time to maturity T
            dividend: Dividend yield q
        """
        self.name = "BlackScholes"
        self.drift = drift - dividend
        self.rate = drift  # Store original drift as rate for discounting
        self.dividend = dividend
        self.volatility = volatility
        self.spot = spot
        self.nb_stocks = nb_stocks
        self.nb_paths = nb_paths
        self.nb_dates = nb_dates
        self.maturity = maturity
        self.dt = self.maturity / self.nb_dates
        self.df = math.exp(-self.rate * self.dt)
        self.return_var = False

    def disc_factor(self, date_begin, date_end):
        """Compute discount factor between two dates."""
        time = (date_end - date_begin) * self.dt
        return math.exp(-self.rate * time)

    def generate_paths(self, nb_paths=None, nb_dates=None, seed=None):
        """
        Generate stock price paths using geometric Brownian motion.

        Args:
            nb_paths: Number of paths (default: self.nb_paths)
            nb_dates: Number of time steps (default: self.nb_dates)
            seed: Random seed for reproducibility

        Returns:
            tuple: (stock_paths, None) where stock_paths has shape
                   (nb_paths, nb_stocks, nb_dates+1)
        """
        if seed is not None:
            np.random.seed(seed)

        nb_paths = nb_paths or self.nb_paths
        nb_dates = nb_dates or self.nb_dates

        # Initialize paths array
        spot_paths = np.empty((nb_paths, self.nb_stocks, nb_dates + 1))
        spot_paths[:, :, 0] = self.spot

        # Generate Brownian increments
        dW = np.random.normal(0, np.sqrt(self.dt),
                              (nb_paths, self.nb_stocks, nb_dates))

        # Vectorized GBM path generation
        # S_t = S_0 * exp((r - q - 0.5*sigma^2)*t + sigma*W_t)
        drift_term = (self.drift - 0.5 * self.volatility**2) * self.dt
        diffusion_term = self.volatility * dW

        # Cumulative sum to get log(S_t / S_0)
        log_returns = np.cumsum(drift_term + diffusion_term, axis=2)

        # Apply exponential to get stock prices
        spot_paths[:, :, 1:] = self.spot * np.exp(log_returns)

        return spot_paths, None
