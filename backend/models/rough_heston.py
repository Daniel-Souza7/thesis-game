"""
Rough Heston model for generating stock price paths.
Variance follows a fractional process with Hurst parameter H < 0.5.
"""

import math
import numpy as np
import scipy.special as scispe


class RoughHeston:
    """
    Rough Heston model with fractional variance process.
    Variance follows a fractional process with Hurst parameter H < 0.5.
    See: "Roughening Heston" paper

    Note: Computationally intensive due to fractional integration.
    """

    def __init__(self, drift, volatility, spot, mean, speed, correlation,
                 nb_stocks, nb_paths, nb_dates, maturity,
                 nb_steps_mult=10, v0=0.026, hurst=0.25, dividend=0, **kwargs):
        """
        Initialize Rough Heston model.

        Args:
            drift: Risk-free rate (r)
            volatility: Volatility of variance process
            spot: Initial stock price S_0
            mean: Long-run variance (theta)
            speed: Mean reversion speed (lambda)
            correlation: Correlation between price and variance
            nb_stocks: Number of stocks (dimension d)
            nb_paths: Number of paths to generate
            nb_dates: Number of exercise dates
            maturity: Time to maturity T
            nb_steps_mult: Fine time discretization multiplier
            v0: Initial variance
            hurst: Hurst parameter (must be < 0.5 for rough)
            dividend: Dividend yield q
        """
        self.name = "RoughHeston"
        self.drift = drift - dividend
        self.rate = drift  # Store original drift for discounting
        self.dividend = dividend
        self.volatility = volatility
        self.spot = spot
        self.mean = mean
        self.speed = speed
        self.correlation = correlation
        self.nb_stocks = nb_stocks
        self.nb_paths = nb_paths
        self.nb_dates = nb_dates
        self.maturity = maturity
        self.nb_steps_mult = nb_steps_mult
        self.return_var = False

        assert 0 < hurst < 0.5, "Rough Heston requires 0 < H < 0.5"
        self.H = hurst

        if v0 is None:
            self.v0 = self.mean
        else:
            self.v0 = v0

        # Fine time discretization
        self.dt = self.maturity / (self.nb_dates * self.nb_steps_mult)
        self.df = math.exp(-self.rate * self.dt)

    def disc_factor(self, date_begin, date_end):
        """Compute discount factor between two dates."""
        time = (date_end - date_begin) * self.dt * self.nb_steps_mult
        return math.exp(-self.rate * time)

    def get_frac_var(self, vars, dZ, step, la, thet, vol):
        """
        Compute next fractional variance value using Euler scheme.

        Args:
            vars: array with previous values of var process
            dZ: array with the BM increments for var process
            step: int > 0, the step of the integral
            la: lambda (mean reversion speed)
            thet: theta (long-run variance)
            vol: volatility of variance

        Returns:
            Next value of fractional var process
        """
        v0 = vars[0]
        times = (self.dt * step - np.linspace(0, self.dt * (step - 1), step)) ** \
                (self.H - 0.5)
        if len(vars.shape) == 2:
            times = np.repeat(np.expand_dims(times, 1), vars.shape[1], axis=1)
        int1 = np.sum(times * la * (thet - vars[:step]) * self.dt, axis=0)
        int2 = np.sum(times * vol * np.sqrt(vars[:step]) * dZ[:step], axis=0)
        v = v0 + (int1 + int2) / scispe.gamma(self.H + 0.5)
        return np.maximum(v, 0)

    def _generate_paths(self, mu, la, thet, vol, start_X, nb_steps, v0=None,
                       nb_stocks=1, seed=None):
        """Generate multiple paths simultaneously (vectorized over stocks)"""
        if seed is not None:
            np.random.seed(seed)

        # Use float32 for memory efficiency
        spot_path = np.empty((nb_steps + 1, nb_stocks), dtype=np.float32)
        spot_path[0] = start_X
        var_path = np.empty((nb_steps + 1, nb_stocks), dtype=np.float32)
        if v0 is None:
            var_path[0] = self.v0
        else:
            var_path[0] = v0

        log_spot_drift = lambda v, t: (mu - 0.5 * np.maximum(v, 0))
        log_spot_diffusion = lambda v: np.sqrt(np.maximum(v, 0))

        # Generate random numbers as float32
        normal_numbers_1 = np.random.normal(0, 1, (nb_steps, nb_stocks)).astype(np.float32)
        normal_numbers_2 = np.random.normal(0, 1, (nb_steps, nb_stocks)).astype(np.float32)
        dW = normal_numbers_1 * np.sqrt(self.dt)
        dZ = (self.correlation * normal_numbers_1 + np.sqrt(
            1 - self.correlation ** 2) * normal_numbers_2) * np.sqrt(self.dt)

        for k in range(1, nb_steps + 1):
            spot_path[k] = np.exp(
                np.log(spot_path[k - 1])
                + log_spot_drift(var_path[k - 1], (k - 1) * self.dt) * self.dt
                + log_spot_diffusion(var_path[k - 1]) * dW[k - 1]
            )
            var_path[k] = self.get_frac_var(var_path, dZ, k, la, thet, vol)

        return spot_path, var_path

    def generate_paths(self, nb_paths=None, nb_dates=None, seed=None):
        """
        Generate stock price paths under P measure.

        Args:
            nb_paths: Number of paths (default: self.nb_paths)
            nb_dates: Number of dates (default: self.nb_dates)
            seed: Random seed for reproducibility

        Returns:
            tuple: (spot_paths, var_paths)
                - spot_paths: shape (nb_paths, nb_stocks, nb_dates+1)
                - var_paths: shape (nb_paths, nb_stocks, nb_dates+1)
        """
        nb_paths = nb_paths or self.nb_paths
        nb_dates = nb_dates or self.nb_dates

        # Generate all paths simultaneously (treating each path*stock as separate)
        spot_paths, var_paths = self._generate_paths(
            self.drift, self.speed, self.mean, self.volatility,
            start_X=self.spot, nb_steps=nb_dates * self.nb_steps_mult,
            nb_stocks=self.nb_stocks * nb_paths,
            seed=seed
        )

        # Downsample to exercise dates only
        spot_paths = spot_paths[0::self.nb_steps_mult]
        var_paths = var_paths[0::self.nb_steps_mult]

        # Reshape to (nb_dates+1, nb_paths, nb_stocks)
        spot_paths = np.reshape(spot_paths,
                                (nb_dates + 1, nb_paths, self.nb_stocks))
        var_paths = np.reshape(var_paths,
                               (nb_dates + 1, nb_paths, self.nb_stocks))

        # Transpose to (nb_paths, nb_stocks, nb_dates+1)
        spot_paths = np.transpose(spot_paths, axes=(1, 2, 0))
        var_paths = np.transpose(var_paths, axes=(1, 2, 0))

        return spot_paths, var_paths
