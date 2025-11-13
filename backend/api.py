"""
Flask API server for the thesis game.

Endpoints:
- GET /api/game/start?product={upandout|dko} - Start a new game
- GET /api/game/info - Get game parameters
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
import pickle
import os
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Paths
DATA_DIR = 'backend/data'
PATHS_DIR = os.path.join(DATA_DIR, 'paths')
MODELS_DIR = os.path.join(DATA_DIR, 'trained_models')

# Global storage for loaded data
GAME_DATA = {}


def load_game_data():
    """Load trained models and test paths on server startup."""
    print("Loading trained models and test paths...")

    # Load UpAndOut Min Put
    try:
        with open(os.path.join(MODELS_DIR, 'upandout_minput.pkl'), 'rb') as f:
            upandout_model = pickle.load(f)

        upandout_test = np.load(os.path.join(PATHS_DIR, 'upandout_test.npz'))
        upandout_paths = upandout_test['paths']

        GAME_DATA['upandout'] = {
            'srlsm': upandout_model['srlsm'],
            'model': upandout_model['model'],
            'payoff': upandout_model['payoff'],
            'test_paths': upandout_paths,
            'price': upandout_model['price'],
            'avg_exercise_time': upandout_model['avg_exercise_time'],
            'name': 'Up-and-Out Min Put',
            'description': 'Put on minimum of 3 stocks with upper barrier at 110',
            'nb_stocks': 3,
            'barrier': 110,
            'barrier_type': 'up'
        }
        print(f"  ✓ Loaded UpAndOut Min Put: {upandout_paths.shape[0]} test paths")
    except Exception as e:
        print(f"  ✗ Failed to load UpAndOut Min Put: {e}")

    # Load DKO Lookback Put
    try:
        with open(os.path.join(MODELS_DIR, 'dko_lookback_put.pkl'), 'rb') as f:
            dko_model = pickle.load(f)

        dko_test = np.load(os.path.join(PATHS_DIR, 'dko_test.npz'))
        dko_paths = dko_test['paths']

        GAME_DATA['dko'] = {
            'srlsm': dko_model['srlsm'],
            'model': dko_model['model'],
            'payoff': dko_model['payoff'],
            'test_paths': dko_paths,
            'price': dko_model['price'],
            'avg_exercise_time': dko_model['avg_exercise_time'],
            'name': 'Double Knock-Out Lookback Put',
            'description': 'Lookback put with barriers at 90 and 110',
            'nb_stocks': 1,
            'barrier_down': 90,
            'barrier_up': 110,
            'barrier_type': 'double'
        }
        print(f"  ✓ Loaded DKO Lookback Put: {dko_paths.shape[0]} test paths")
    except Exception as e:
        print(f"  ✗ Failed to load DKO Lookback Put: {e}")

    print(f"\nLoaded {len(GAME_DATA)} games successfully!")


@app.route('/api/game/info', methods=['GET'])
def get_game_info():
    """Get information about available games."""
    games = {}
    for key, data in GAME_DATA.items():
        games[key] = {
            'name': data['name'],
            'description': data['description'],
            'nb_stocks': data['nb_stocks'],
            'strike': data['model'].spot,
            'maturity': data['model'].maturity,
            'nb_dates': data['model'].nb_dates,
            'price': float(data['price']),
            'avg_exercise_time': float(data['avg_exercise_time'])
        }

        if 'barrier' in data:
            games[key]['barrier'] = data['barrier']
        if 'barrier_down' in data:
            games[key]['barrier_down'] = data['barrier_down']
        if 'barrier_up' in data:
            games[key]['barrier_up'] = data['barrier_up']

    return jsonify(games)


@app.route('/api/game/start', methods=['GET'])
def start_game():
    """
    Start a new game by selecting a random test path and computing machine decisions.

    Query params:
        product: 'upandout' or 'dko'

    Returns:
        {
            'game_id': str,
            'path': list[list[float]],  # [nb_stocks][nb_dates+1]
            'machine_decisions': list[bool],  # Exercise decision at each date
            'machine_exercise_date': int,
            'payoffs_timeline': list[float],  # Payoff at each date
            'game_info': {...}
        }
    """
    product = request.args.get('product', 'upandout')

    if product not in GAME_DATA:
        return jsonify({'error': f'Invalid product: {product}'}), 400

    game = GAME_DATA[product]

    # Select a random test path
    test_paths = game['test_paths']
    path_idx = random.randint(0, len(test_paths) - 1)
    selected_path = test_paths[path_idx:path_idx+1]  # Shape: (1, nb_stocks, nb_dates+1)

    # Predict machine exercise decision
    srlsm = game['srlsm']
    payoff = game['payoff']
    model = game['model']

    exercise_dates = srlsm.predict_exercise_decisions(selected_path)
    machine_exercise_date = int(exercise_dates[0])

    # Compute payoffs at each timestep
    nb_dates = selected_path.shape[2] - 1
    payoffs_timeline = []
    machine_decisions = []

    for t in range(nb_dates + 1):
        path_up_to_t = selected_path[:, :, :t+1]
        payoff_t = payoff.eval(path_up_to_t)[0]
        payoffs_timeline.append(float(payoff_t))

        # Machine exercises if this is the exercise date
        machine_decisions.append(t == machine_exercise_date)

    # Convert path to list format for JSON
    # Shape: (nb_stocks, nb_dates+1)
    path_list = selected_path[0].tolist()

    # Game metadata
    game_info = {
        'name': game['name'],
        'description': game['description'],
        'nb_stocks': game['nb_stocks'],
        'nb_dates': nb_dates,
        'strike': float(model.spot),
        'maturity': float(model.maturity),
        'dt': float(model.dt)
    }

    if 'barrier' in game:
        game_info['barrier'] = game['barrier']
        game_info['barrier_type'] = 'up'
    if 'barrier_down' in game:
        game_info['barrier_down'] = game['barrier_down']
        game_info['barrier_up'] = game['barrier_up']
        game_info['barrier_type'] = 'double'

    return jsonify({
        'game_id': f"{product}_{path_idx}",
        'path': path_list,
        'machine_decisions': machine_decisions,
        'machine_exercise_date': machine_exercise_date,
        'payoffs_timeline': payoffs_timeline,
        'game_info': game_info
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'games_loaded': list(GAME_DATA.keys())
    })


if __name__ == '__main__':
    # Load data on startup
    load_game_data()

    # Start server
    print("\nStarting API server on http://localhost:5000")
    print("Endpoints:")
    print("  GET /api/health")
    print("  GET /api/game/info")
    print("  GET /api/game/start?product={upandout|dko}")
    print("\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
