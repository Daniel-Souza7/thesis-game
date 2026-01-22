"""Game Payoffs - Special challenge payoffs with varying difficulty levels.

These payoffs combine multiple concepts like barriers, lookbacks, and custom basket calculations.
Difficulty levels: MEDIUM, HARD, IMPOSSIBLE

Key principles:
- All payoffs evaluate at time t (not T) - American-style early exercise
- Barrier checks use min/max across ALL stocks AND ALL time up to t
- For moving barriers, check S(τ) vs B(τ) at each specific time τ
"""

import numpy as np
from backend.payoffs.barrier_options import Payoff


# ============================================================================
# MEDIUM DIFFICULTY
# ============================================================================

class UpAndOutCall(Payoff):
    """Up-and-out call option for a single stock.

    Barrier: max_{τ≤t} S(τ) < B_U
    Payoff: max(S(t) - K, 0) if barrier not hit, else 0

    Difficulty: MEDIUM
    Stocks: 1
    """
    is_path_dependent = True

    def __init__(self, strike, barrier):
        super().__init__(strike)
        self.barrier = barrier

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, 1, t+1) - price path up to time t
        """
        # Check if maximum price up to time t exceeds barrier
        max_price_up_to_t = np.max(X[:, 0, :], axis=1)
        knocked_out = max_price_up_to_t >= self.barrier

        # Payoff at time t
        price_at_t = X[:, 0, -1]
        payoff = np.maximum(0, price_at_t - self.strike)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


class DownAndOutMinPut(Payoff):
    """Down-and-out put on minimum of stocks.

    Barrier: min_{τ≤t,i} S_i(τ) > B_L
    Payoff: max(K - min_i S_i(t), 0) if barrier not hit, else 0

    Difficulty: MEDIUM
    Stocks: Multiple
    """
    is_path_dependent = True

    def __init__(self, strike, barrier):
        super().__init__(strike)
        self.barrier = barrier

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, nb_stocks, t+1)
        """
        # Check if minimum price across all stocks and time goes below barrier
        min_price_overall = np.min(X, axis=(1, 2))  # min over stocks and time
        knocked_out = min_price_overall <= self.barrier

        # Payoff: put on minimum at time t
        min_at_t = np.min(X[:, :, -1], axis=1)
        payoff = np.maximum(0, self.strike - min_at_t)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


class DoubleBarrierMaxCall(Payoff):
    """Double barrier call on maximum of stocks.

    Barrier: min_{τ≤t,i} S_i(τ) > B_L AND max_{τ≤t,i} S_i(τ) < B_U
    Payoff: max(max_i S_i(t) - K, 0) if barriers not hit, else 0

    Difficulty: MEDIUM
    Stocks: Multiple
    """
    is_path_dependent = True

    def __init__(self, strike, barrier_up, barrier_down):
        super().__init__(strike)
        self.barrier_up = barrier_up
        self.barrier_down = barrier_down

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, nb_stocks, t+1)
        """
        # Check barriers across all stocks and time
        max_overall = np.max(X, axis=(1, 2))  # max over stocks and time
        min_overall = np.min(X, axis=(1, 2))  # min over stocks and time

        knocked_out = (max_overall >= self.barrier_up) | (min_overall <= self.barrier_down)

        # Payoff: max of all stocks at time t
        max_at_t = np.max(X[:, :, -1], axis=1)
        payoff = np.maximum(0, max_at_t - self.strike)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


# ============================================================================
# HARD DIFFICULTY
# ============================================================================

class StepBarrierCall(Payoff):
    """Call option with stochastic step barrier (upper only).

    Moving Barrier: B_U(τ+1) = B_U(τ) + uniform(-2, 1)
    Barrier: For all τ≤t, check if S(τ) < B_U(τ)
    Payoff: max(S(t) - K, 0) if never hit barrier, else 0

    Difficulty: HARD
    Stocks: 1
    """
    is_path_dependent = True

    def __init__(self, strike, initial_barrier, seed=42):
        super().__init__(strike)
        self.initial_barrier = initial_barrier
        self.seed = seed

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, 1, t+1)
        """
        nb_paths, nb_stocks, t_plus_1 = X.shape
        t = t_plus_1 - 1

        # Generate barrier path up to time t (deterministic based on seed)
        rng = np.random.RandomState(self.seed)
        barrier_steps = rng.uniform(-2, 1, size=t).astype(np.float32)
        barrier_path = np.zeros(t_plus_1, dtype=np.float32)
        barrier_path[0] = self.initial_barrier

        for tau in range(1, t_plus_1):
            barrier_path[tau] = barrier_path[tau-1] + barrier_steps[tau-1]

        # Get stock prices
        prices = X[:, 0, :]  # (nb_paths, t+1)

        # Check if price ever exceeds the time-varying barrier
        # At each time τ, check if S(τ) >= B(τ)
        knocked_out = np.any(prices >= barrier_path[np.newaxis, :], axis=1)

        # Payoff at time t
        price_at_t = prices[:, -1]
        payoff = np.maximum(0, price_at_t - self.strike)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


class GameUpAndOutMinPut(Payoff):
    """Up-and-out put on minimum of stocks.

    Barrier: max_{τ≤t,i} S_i(τ) < B_U
    Payoff: max(K - min_i S_i(t), 0) if barrier not hit, else 0

    Difficulty: HARD
    Stocks: Multiple
    """
    is_path_dependent = True

    def __init__(self, strike, barrier):
        super().__init__(strike)
        self.barrier = barrier

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, nb_stocks, t+1)
        """
        # Check if maximum across all stocks and time goes above barrier
        max_overall = np.max(X, axis=(1, 2))  # max over stocks and time
        knocked_out = max_overall >= self.barrier

        # Payoff: put on minimum at time t
        min_at_t = np.min(X[:, :, -1], axis=1)
        payoff = np.maximum(0, self.strike - min_at_t)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


class DownAndOutBestOfKCall(Payoff):
    """Down-and-out call on the average of the top K stocks.

    Barrier: min_{τ≤t,i} S_i(τ) > B_L
    Best-of-K: avg(top K stocks at time t)
    Payoff: max(avg(top K at t) - K, 0) if barrier not hit, else 0

    Difficulty: HARD
    Stocks: Multiple (at least k stocks)
    """
    is_path_dependent = True

    def __init__(self, strike, barrier, k=2):
        super().__init__(strike)
        self.barrier = barrier
        self.k = k

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, nb_stocks, t+1)
        """
        # Check if minimum across all stocks and time goes below barrier
        min_overall = np.min(X, axis=(1, 2))  # min over stocks and time
        knocked_out = min_overall <= self.barrier

        # Payoff: average of top k stocks at time t
        prices_at_t = X[:, :, -1]  # (nb_paths, nb_stocks)
        sorted_prices = np.sort(prices_at_t, axis=1)[:, ::-1]  # Sort descending
        top_k_avg = np.mean(sorted_prices[:, :self.k], axis=1)

        payoff = np.maximum(0, top_k_avg - self.strike)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


# ============================================================================
# IMPOSSIBLE DIFFICULTY
# ============================================================================

class DoubleBarrierLookbackFloatingPut(Payoff):
    """Double barrier lookback floating strike put.

    Barrier: min_{τ≤t} S(τ) > B_L AND max_{τ≤t} S(τ) < B_U
    Lookback: max_{τ≤t} S(τ) - S(t)
    Payoff: max(max_{τ≤t} S(τ) - S(t), 0) if barriers not hit, else 0

    Difficulty: IMPOSSIBLE
    Stocks: 1
    """
    is_path_dependent = True

    def __init__(self, strike, barrier_up, barrier_down):
        super().__init__(strike)
        self.barrier_up = barrier_up
        self.barrier_down = barrier_down

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, 1, t+1)
        """
        prices = X[:, 0, :]  # (nb_paths, t+1)

        # Check double barrier
        max_price = np.max(prices, axis=1)
        min_price = np.min(prices, axis=1)
        knocked_out = (max_price >= self.barrier_up) | (min_price <= self.barrier_down)

        # Lookback floating put payoff at time t
        max_up_to_t = np.max(prices, axis=1)
        price_at_t = prices[:, -1]
        payoff = np.maximum(0, max_up_to_t - price_at_t)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


class DoubleBarrierRankWeightedBasketCall(Payoff):
    """Double barrier call on rank-weighted basket of exactly 3 stocks.

    Barrier: min_{τ≤t,i} S_i(τ) > B_L AND max_{τ≤t,i} S_i(τ) < B_U
    Weighted Basket: Rank stocks at time t, apply weights [15%, 50%, 35%] for [1st, 2nd, 3rd]
    Payoff: max(weighted_basket(t) - K, 0) if barriers not hit, else 0

    Difficulty: IMPOSSIBLE
    Stocks: Exactly 3
    """
    is_path_dependent = True

    def __init__(self, strike, barrier_up, barrier_down):
        super().__init__(strike)
        self.barrier_up = barrier_up
        self.barrier_down = barrier_down
        # Weights: [1st place, 2nd place, 3rd place]
        self.weights = np.array([0.15, 0.50, 0.35])

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, 3, t+1) - exactly 3 stocks required
        """
        nb_paths, nb_stocks, t_plus_1 = X.shape
        assert nb_stocks == 3, "DoubleBarrierRankWeightedBasketCall requires exactly 3 stocks"

        # Check double barrier across all stocks and time
        max_overall = np.max(X, axis=(1, 2))
        min_overall = np.min(X, axis=(1, 2))
        knocked_out = (max_overall >= self.barrier_up) | (min_overall <= self.barrier_down)

        # Calculate rank-weighted basket at time t
        prices_at_t = X[:, :, -1]  # (nb_paths, 3)

        # Sort prices in descending order (rank 1 = highest)
        sorted_prices = np.sort(prices_at_t, axis=1)[:, ::-1]  # (nb_paths, 3)

        # Apply weights: 1st=15%, 2nd=50%, 3rd=35%
        weighted_basket = np.sum(sorted_prices * self.weights[np.newaxis, :], axis=1)

        payoff = np.maximum(0, weighted_basket - self.strike)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff


class DoubleStepBarrierDispersionCall(Payoff):
    """Dispersion call with double stochastic step barriers.

    Moving Barriers:
      B_L(τ+1) = B_L(τ) + uniform(-1, 2)
      B_U(τ+1) = B_U(τ) + uniform(-2, 1)
    Barrier: For all τ≤t, check if max_i S_i(τ) < B_U(τ) AND min_i S_i(τ) > B_L(τ)
             (knocked out if any individual stock breaches either barrier)
    Dispersion: std_dev(S_1(t), ..., S_d(t)) = sqrt(mean((S_i - avg(S))^2))
    Payoff: max(std_dev(t) - K, 0) if never hit barriers, else 0

    Difficulty: IMPOSSIBLE
    Stocks: Multiple
    """
    is_path_dependent = True

    def __init__(self, strike, barrier_up, barrier_down, seed=42):
        super().__init__(strike)
        self.barrier_up = barrier_up
        self.barrier_down = barrier_down
        self.seed = seed

    def eval(self, X):
        """Evaluate payoff at time t.

        Args:
            X: shape (nb_paths, nb_stocks, t+1)
        """
        nb_paths, nb_stocks, t_plus_1 = X.shape
        t = t_plus_1 - 1

        # Generate stochastic barrier paths up to time t
        rng = np.random.RandomState(self.seed)

        # Lower barrier: adds uniform(-1, 2) at each step
        lower_steps = rng.uniform(-1, 2, size=t).astype(np.float32)
        lower_barrier_path = np.zeros(t_plus_1, dtype=np.float32)
        lower_barrier_path[0] = self.barrier_down

        for tau in range(1, t_plus_1):
            lower_barrier_path[tau] = lower_barrier_path[tau-1] + lower_steps[tau-1]

        # Upper barrier: adds uniform(-2, 1) at each step
        upper_steps = rng.uniform(-2, 1, size=t).astype(np.float32)
        upper_barrier_path = np.zeros(t_plus_1, dtype=np.float32)
        upper_barrier_path[0] = self.barrier_up

        for tau in range(1, t_plus_1):
            upper_barrier_path[tau] = upper_barrier_path[tau-1] + upper_steps[tau-1]

        # Check individual stock prices against moving barriers
        # Upper barrier: knocked out if max stock >= barrier at any time
        # Lower barrier: knocked out if min stock <= barrier at any time
        max_prices = np.max(X, axis=1)  # (nb_paths, t+1) - max across stocks at each time
        min_prices = np.min(X, axis=1)  # (nb_paths, t+1) - min across stocks at each time

        # Check if any stock breaches barriers at any time τ
        breaches_upper = np.any(max_prices >= upper_barrier_path[np.newaxis, :], axis=1)
        breaches_lower = np.any(min_prices <= lower_barrier_path[np.newaxis, :], axis=1)
        knocked_out = breaches_upper | breaches_lower

        # Dispersion payoff at time t: std_dev(S_1(t), ..., S_d(t)) - K
        prices_at_t = X[:, :, -1]  # (nb_paths, nb_stocks)

        # Calculate dispersion: standard deviation across stocks
        mean_price = np.mean(prices_at_t, axis=1, keepdims=True)  # (nb_paths, 1)
        std_dev = np.sqrt(np.mean((prices_at_t - mean_price) ** 2, axis=1))  # (nb_paths,)

        payoff = np.maximum(0, std_dev - self.strike)

        # Zero out knocked-out paths
        payoff[knocked_out] = 0

        return payoff
