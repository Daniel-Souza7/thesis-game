"""
Quick test to verify basic functionality of the models and algorithms.
"""

import sys
import numpy as np

print("Testing basic functionality...\n")

# Test 1: Import modules
print("1. Testing imports...")
try:
    from backend.models.black_scholes import BlackScholes
    from backend.payoffs.barrier_options import UpAndOutMinPut, DoubleKnockOutLookbackFloatingPut
    from backend.algorithms.srlsm import SRLSM
    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Black-Scholes path generation
print("\n2. Testing Black-Scholes path generation...")
try:
    model = BlackScholes(
        drift=0.02,
        volatility=0.2,
        spot=100,
        nb_stocks=3,
        nb_paths=100,
        nb_dates=10,
        maturity=1,
        dividend=0
    )
    paths, _ = model.generate_paths(seed=42)
    assert paths.shape == (100, 3, 11), f"Expected shape (100, 3, 11), got {paths.shape}"
    assert np.all(paths[:, :, 0] == 100), "Initial prices should be 100"
    print(f"   ✓ Generated paths with shape {paths.shape}")
except Exception as e:
    print(f"   ✗ Path generation error: {e}")
    sys.exit(1)

# Test 3: UpAndOut payoff evaluation
print("\n3. Testing UpAndOut Min Put payoff...")
try:
    payoff = UpAndOutMinPut(strike=100, barrier=110)
    test_payoffs = payoff.eval(paths)
    assert test_payoffs.shape == (100,), f"Expected shape (100,), got {test_payoffs.shape}"
    assert np.all(test_payoffs >= 0), "Payoffs should be non-negative"
    print(f"   ✓ Payoffs computed, mean: {np.mean(test_payoffs):.2f}")
except Exception as e:
    print(f"   ✗ Payoff evaluation error: {e}")
    sys.exit(1)

# Test 4: DKO Lookback payoff evaluation
print("\n4. Testing DKO Lookback Put payoff...")
try:
    model_1stock = BlackScholes(
        drift=0.02,
        volatility=0.2,
        spot=100,
        nb_stocks=1,
        nb_paths=100,
        nb_dates=10,
        maturity=1,
        dividend=0
    )
    paths_1stock, _ = model_1stock.generate_paths(seed=43)

    payoff_dko = DoubleKnockOutLookbackFloatingPut(strike=100, barrier_down=90, barrier_up=110)
    test_payoffs_dko = payoff_dko.eval(paths_1stock)
    assert test_payoffs_dko.shape == (100,), f"Expected shape (100,), got {test_payoffs_dko.shape}"
    assert np.all(test_payoffs_dko >= 0), "Payoffs should be non-negative"
    print(f"   ✓ Payoffs computed, mean: {np.mean(test_payoffs_dko):.2f}")
except Exception as e:
    print(f"   ✗ DKO payoff evaluation error: {e}")
    sys.exit(1)

# Test 5: SRLSM initialization (small test)
print("\n5. Testing SRLSM initialization...")
try:
    model_small = BlackScholes(
        drift=0.02,
        volatility=0.2,
        spot=100,
        nb_stocks=3,
        nb_paths=500,  # Small for quick test
        nb_dates=10,
        maturity=1,
        dividend=0
    )

    payoff_test = UpAndOutMinPut(strike=100, barrier=110)

    srlsm = SRLSM(
        model=model_small,
        payoff=payoff_test,
        hidden_size=20,
        factors=(1.0, 1.0, 1.0),
        train_ITM_only=True,
        use_payoff_as_input=False
    )

    print("   ✓ SRLSM initialized successfully")

    # Quick pricing test
    print("\n6. Testing SRLSM pricing (small dataset)...")
    price, time_gen = srlsm.price(train_eval_split=2)
    avg_ex_time = srlsm.get_exercise_time()

    print(f"   ✓ SRLSM pricing complete")
    print(f"   ✓ Option price: {price:.4f}")
    print(f"   ✓ Avg exercise time: {avg_ex_time:.4f}")

except Exception as e:
    print(f"   ✗ SRLSM error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("All tests passed! ✓")
print("="*60)
print("\nYou can now run the full training script:")
print("  python backend/train_models.py")
