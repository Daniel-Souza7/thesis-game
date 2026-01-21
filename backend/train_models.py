"""
Pre-training script for RT models and path generation.

This script:
1. Generates shared training paths (12,000) for each stock count (1, 3, 7)
2. Trains RT models for all 9 games using shared paths
3. Generates shared test paths (2,000) for each stock count
4. Saves models and paths to disk

Run this BEFORE starting the API server.
"""

import numpy as np
import pickle
import os
from backend.models.rough_heston import RoughHeston
from backend.payoffs.game_payoffs import (
    # MEDIUM
    UpAndOutCall,
    DownAndOutMinPut,
    DoubleBarrierMaxCall,
    # HARD
    StepBarrierCall,
    GameUpAndOutMinPut,
    DownAndOutBestOfKCall,
    # IMPOSSIBLE
    DoubleBarrierLookbackFloatingPut,
    DoubleBarrierRankWeightedBasketCall,
    DoubleStepBarrierDispersionCall
)
from backend.algorithms.rt import RT


# Game parameters - Rough Heston model
PARAMS = {
    'drift': 0.02,
    'volatility': 0.29,
    'mean': 0.07,
    'speed': 0.5,
    'correlation': -0.75,
    'hurst': 0.03,
    'spot': 100,
    'strike': 100,  # K=100 for all games
    'dividend': 0,
    'maturity': 1,
    'nb_dates': 12,
    'hidden_size': 40,  # RT default
    'factors': (1.0, 1.0, 1.0),
    'train_ITM_only': True,
    'use_payoff_as_input': True,  # RT default
    'use_barrier_as_input': False,
    'activation': 'gelu',  # RT default
    'dropout': 0.0,
    'v0': 0.026,
    'nb_steps_mult': 10
}

# Training and test set sizes
NB_TRAIN_PATHS = 12000
NB_TEST_PATHS = 2000

# Output directories (relative to this script's location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
PATHS_DIR = os.path.join(DATA_DIR, 'paths')
MODELS_DIR = os.path.join(DATA_DIR, 'trained_models')


# Game configurations in order
GAME_CONFIGS = [
    # MEDIUM
    {
        'id': 'upandoutcall',
        'name': 'UpAndOutCall',
        'nb_stocks': 1,
        'difficulty': 'Medium',
        'payoff_class': UpAndOutCall,
        'payoff_kwargs': {'strike': 100, 'barrier': 120}
    },
    {
        'id': 'downandoutminput',
        'name': 'DownAndOutMinPut',
        'nb_stocks': 3,
        'difficulty': 'Medium',
        'payoff_class': DownAndOutMinPut,
        'payoff_kwargs': {'strike': 100, 'barrier': 85}
    },
    {
        'id': 'doublebarriermaxcall',
        'name': 'DoubleBarrierMaxCall',
        'nb_stocks': 7,
        'difficulty': 'Medium',
        'payoff_class': DoubleBarrierMaxCall,
        'payoff_kwargs': {'strike': 100, 'barrier_up': 130, 'barrier_down': 85}
    },
    # HARD
    {
        'id': 'randomlymovingbarriercall',
        'name': 'RandomlyMovingBarrierCall',
        'nb_stocks': 1,
        'difficulty': 'Hard',
        'payoff_class': StepBarrierCall,
        'payoff_kwargs': {'strike': 100, 'initial_barrier': 125, 'seed': 42}
    },
    {
        'id': 'upandoutminput',
        'name': 'UpAndOutMinPut',
        'nb_stocks': 3,
        'difficulty': 'Hard',
        'payoff_class': GameUpAndOutMinPut,
        'payoff_kwargs': {'strike': 100, 'barrier': 120}
    },
    {
        'id': 'downandoutbest2call',
        'name': 'DownAndOutBest2Call',
        'nb_stocks': 7,
        'difficulty': 'Hard',
        'payoff_class': DownAndOutBestOfKCall,
        'payoff_kwargs': {'strike': 100, 'barrier': 85, 'k': 2}
    },
    # IMPOSSIBLE
    {
        'id': 'doublebarrierlookbackfloatingput',
        'name': 'DoubleBarrierLookbackFloatingPut',
        'nb_stocks': 1,
        'difficulty': 'Impossible',
        'payoff_class': DoubleBarrierLookbackFloatingPut,
        'payoff_kwargs': {'strike': 100, 'barrier_up': 115, 'barrier_down': 85}
    },
    {
        'id': 'doublebarrierrankweightedbskcall',
        'name': 'DoubleBarrierRankWeightedBskCall',
        'nb_stocks': 3,
        'difficulty': 'Impossible',
        'payoff_class': DoubleBarrierRankWeightedBasketCall,
        'payoff_kwargs': {'strike': 100, 'barrier_up': 125, 'barrier_down': 80}
    },
    {
        'id': 'doublemovingbarrierdispersioncall',
        'name': 'DoubleMovingBarrierDispersionCall',
        'nb_stocks': 7,
        'difficulty': 'Impossible',
        'payoff_class': DoubleStepBarrierDispersionCall,
        'payoff_kwargs': {'strike': 100, 'barrier_up': 115, 'barrier_down': 85, 'seed': 42}
    }
]


def generate_shared_paths(nb_stocks, train_seed, test_seed):
    """Generate shared training and test paths for a given number of stocks."""
    print(f"\n{'='*60}")
    print(f"Generating shared paths for {nb_stocks} stock(s)")
    print(f"{'='*60}")

    # Create Rough Heston model for training paths
    model = RoughHeston(
        drift=PARAMS['drift'],
        volatility=PARAMS['volatility'],
        mean=PARAMS['mean'],
        speed=PARAMS['speed'],
        correlation=PARAMS['correlation'],
        hurst=PARAMS['hurst'],
        spot=PARAMS['spot'],
        nb_stocks=nb_stocks,
        nb_paths=NB_TRAIN_PATHS,
        nb_dates=PARAMS['nb_dates'],
        maturity=PARAMS['maturity'],
        dividend=PARAMS['dividend'],
        v0=PARAMS['v0'],
        nb_steps_mult=PARAMS['nb_steps_mult']
    )

    # Generate training paths
    print(f"Generating {NB_TRAIN_PATHS} training paths...")
    train_paths, _ = model.generate_paths(seed=train_seed)
    train_path_file = os.path.join(PATHS_DIR, f'train_{nb_stocks}stock.npz')
    np.savez_compressed(train_path_file, paths=train_paths)
    print(f"Saved training paths to {train_path_file}")
    print(f"Shape: {train_paths.shape}")

    # Generate test paths
    print(f"Generating {NB_TEST_PATHS} test paths...")
    model.nb_paths = NB_TEST_PATHS
    test_paths, _ = model.generate_paths(seed=test_seed)
    test_path_file = os.path.join(PATHS_DIR, f'test_{nb_stocks}stock.npz')
    np.savez_compressed(test_path_file, paths=test_paths)
    print(f"Saved test paths to {test_path_file}")
    print(f"Shape: {test_paths.shape}")

    return train_paths, test_paths


def train_game(config, train_paths):
    """Train RT for a specific game configuration."""
    print(f"\n{'='*60}")
    print(f"Training {config['name']} ({config['difficulty']})")
    print(f"{'='*60}")

    # Create Rough Heston model
    model = RoughHeston(
        drift=PARAMS['drift'],
        volatility=PARAMS['volatility'],
        mean=PARAMS['mean'],
        speed=PARAMS['speed'],
        correlation=PARAMS['correlation'],
        hurst=PARAMS['hurst'],
        spot=PARAMS['spot'],
        nb_stocks=config['nb_stocks'],
        nb_paths=NB_TRAIN_PATHS,
        nb_dates=PARAMS['nb_dates'],
        maturity=PARAMS['maturity'],
        dividend=PARAMS['dividend'],
        v0=PARAMS['v0'],
        nb_steps_mult=PARAMS['nb_steps_mult']
    )

    # Create payoff
    payoff = config['payoff_class'](**config['payoff_kwargs'])

    # Train RT
    print("Training RT model...")
    rt = RT(
        model=model,
        payoff=payoff,
        hidden_size=PARAMS['hidden_size'],
        factors=PARAMS['factors'],
        train_ITM_only=PARAMS['train_ITM_only'],
        use_payoff_as_input=PARAMS['use_payoff_as_input'],
        use_barrier_as_input=PARAMS['use_barrier_as_input'],
        activation=PARAMS['activation'],
        dropout=PARAMS['dropout']
    )

    price, time_gen = rt.price(train_eval_split=2, stock_paths=train_paths)
    avg_exercise_time = rt.get_exercise_time()

    print(f"\nTraining complete!")
    print(f"  Option price: {price:.4f}")
    print(f"  Average exercise time: {avg_exercise_time:.4f}")

    # Save trained model
    model_file = os.path.join(MODELS_DIR, f"{config['id']}.pkl")
    with open(model_file, 'wb') as f:
        pickle.dump({
            'rt': rt,
            'model': model,
            'payoff': payoff,
            'price': price,
            'avg_exercise_time': avg_exercise_time,
            'config': config
        }, f)
    print(f"Saved trained model to {model_file}")

    return rt


def main():
    """Main training script."""
    print("\n" + "="*60)
    print("RT Model Training Script - All 9 Games (Rough Heston)")
    print("="*60)
    print(f"\nModel: Rough Heston")
    print(f"Parameters:")
    for key, value in PARAMS.items():
        print(f"  {key}: {value}")
    print(f"\nTraining paths: {NB_TRAIN_PATHS}")
    print(f"Test paths: {NB_TEST_PATHS}")
    print(f"\nGames to train: {len(GAME_CONFIGS)}")

    # Create output directories
    os.makedirs(PATHS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Generate shared paths for each stock count
    shared_paths = {}

    # 1 stock paths (seed 42 for train, 142 for test)
    train_1stock, test_1stock = generate_shared_paths(1, train_seed=42, test_seed=142)
    shared_paths[1] = {'train': train_1stock, 'test': test_1stock}

    # 3 stock paths (seed 43 for train, 143 for test)
    train_3stock, test_3stock = generate_shared_paths(3, train_seed=43, test_seed=143)
    shared_paths[3] = {'train': train_3stock, 'test': test_3stock}

    # 7 stock paths (seed 44 for train, 144 for test)
    train_7stock, test_7stock = generate_shared_paths(7, train_seed=44, test_seed=144)
    shared_paths[7] = {'train': train_7stock, 'test': test_7stock}

    # Train all games
    print(f"\n{'='*60}")
    print("Training all games...")
    print(f"{'='*60}")

    for config in GAME_CONFIGS:
        nb_stocks = config['nb_stocks']
        train_paths = shared_paths[nb_stocks]['train']
        train_game(config, train_paths)

    print("\n" + "="*60)
    print("All 9 models trained successfully!")
    print("="*60)
    print(f"\nSaved to:")
    print(f"  Models: {MODELS_DIR}")
    print(f"  Paths: {PATHS_DIR}")
    print("\nYou can now start the API server.")


if __name__ == '__main__':
    main()
