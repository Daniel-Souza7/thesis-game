"""
Flask API server for the thesis game.

Endpoints:
- GET /api/game/start?product={game_id} - Start a new game
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

# Paths (relative to this script's location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
PATHS_DIR = os.path.join(DATA_DIR, 'paths')
MODELS_DIR = os.path.join(DATA_DIR, 'trained_models')

# Global storage for loaded data
GAME_DATA = {}

# Game configurations matching train_models.py
GAME_CONFIGS = [
    # MEDIUM
    {
        'id': 'upandoutcall',
        'name': 'UpAndOutCall',
        'description': '1 stock, upper barrier at 130',
        'nb_stocks': 1,
        'difficulty': 'Medium',
        'barrier': 130,
        'barrier_type': 'up'
    },
    {
        'id': 'downandoutminput',
        'name': 'DownAndOutMinPut',
        'description': '3 stocks, lower barrier at 85',
        'nb_stocks': 3,
        'difficulty': 'Medium',
        'barrier': 85,
        'barrier_type': 'down'
    },
    {
        'id': 'doublebarriermaxcall',
        'name': 'DoubleBarrierMaxCall',
        'description': '7 stocks, barriers at 85 and 130',
        'nb_stocks': 7,
        'difficulty': 'Medium',
        'barrier_up': 130,
        'barrier_down': 85,
        'barrier_type': 'double'
    },
    # HARD
    {
        'id': 'randomlymovingbarriercall',
        'name': 'RandomlyMovingBarrierCall',
        'description': '1 stock, moving barrier starting at 125',
        'nb_stocks': 1,
        'difficulty': 'Hard',
        'barrier': 125,
        'barrier_type': 'up'
    },
    {
        'id': 'upandoutminput',
        'name': 'UpAndOutMinPut',
        'description': '3 stocks, upper barrier at 120',
        'nb_stocks': 3,
        'difficulty': 'Hard',
        'barrier': 120,
        'barrier_type': 'up'
    },
    {
        'id': 'downandoutbest2call',
        'name': 'DownAndOutBest2Call',
        'description': '7 stocks, lower barrier at 85',
        'nb_stocks': 7,
        'difficulty': 'Hard',
        'barrier': 85,
        'barrier_type': 'down'
    },
    # IMPOSSIBLE
    {
        'id': 'doublebarrierlookbackfloatingput',
        'name': 'DoubleBarrierLookbackFloatingPut',
        'description': '1 stock, barriers at 85 and 115',
        'nb_stocks': 1,
        'difficulty': 'Impossible',
        'barrier_up': 115,
        'barrier_down': 85,
        'barrier_type': 'double'
    },
    {
        'id': 'doublebarrierrankweightedbskcall',
        'name': 'DoubleBarrierRankWeightedBskCall',
        'description': '3 stocks, barriers at 80 and 125',
        'nb_stocks': 3,
        'difficulty': 'Impossible',
        'barrier_up': 125,
        'barrier_down': 80,
        'barrier_type': 'double'
    },
    {
        'id': 'doublemovingbarrierdispersioncall',
        'name': 'DoubleMovingBarrierDispersionCall',
        'description': '7 stocks, moving barriers at 85 and 115',
        'nb_stocks': 7,
        'difficulty': 'Impossible',
        'barrier_up': 115,
        'barrier_down': 85,
        'barrier_type': 'double'
    }
]


def load_game_data():
    """Load trained models and test paths on server startup."""
    print("Loading trained models and test paths...")

    # Load shared test paths for each stock count
    test_paths_by_stock = {}
    for nb_stocks in [1, 3, 7]:
        try:
            test_data = np.load(os.path.join(PATHS_DIR, f'test_{nb_stocks}stock.npz'))
            test_paths_by_stock[nb_stocks] = test_data['paths']
            print(f"  ✓ Loaded test paths for {nb_stocks} stock(s): {test_data['paths'].shape[0]} paths")
        except Exception as e:
            print(f"  ✗ Failed to load test paths for {nb_stocks} stock(s): {e}")

    # Load each game's trained model
    for config in GAME_CONFIGS:
        game_id = config['id']
        try:
            # Load trained model
            model_file = os.path.join(MODELS_DIR, f"{game_id}.pkl")
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)

            # Get test paths for this stock count
            nb_stocks = config['nb_stocks']
            test_paths = test_paths_by_stock.get(nb_stocks)

            if test_paths is None:
                print(f"  ✗ No test paths available for {game_id}")
                continue

            # Store game data
            GAME_DATA[game_id] = {
                'srlsm': model_data['srlsm'],
                'model': model_data['model'],
                'payoff': model_data['payoff'],
                'test_paths': test_paths,
                'price': model_data['price'],
                'avg_exercise_time': model_data['avg_exercise_time'],
                'name': config['name'],
                'description': config['description'],
                'nb_stocks': config['nb_stocks'],
                'difficulty': config['difficulty'],
                'barrier_type': config['barrier_type']
            }

            # Add barrier information
            if 'barrier' in config:
                GAME_DATA[game_id]['barrier'] = config['barrier']
            if 'barrier_up' in config:
                GAME_DATA[game_id]['barrier_up'] = config['barrier_up']
            if 'barrier_down' in config:
                GAME_DATA[game_id]['barrier_down'] = config['barrier_down']

            print(f"  ✓ Loaded {config['name']}")
        except Exception as e:
            print(f"  ✗ Failed to load {config['name']}: {e}")

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
            'difficulty': data['difficulty'],
            'strike': 100,  # K=100 for all games
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
        product: game ID (e.g., 'upandoutcall', 'downandoutbskput', etc.)

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
    product = request.args.get('product', 'upandoutcall')

    if product not in GAME_DATA:
        return jsonify({'error': f'Invalid product: {product}. Available: {list(GAME_DATA.keys())}'}), 400

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

    # Generate barrier paths for moving barrier games
    barrier_path = None
    barrier_path_upper = None
    barrier_path_lower = None

    if product == 'randomlymovingbarriercall':
        # StepBarrierCall: single upper barrier
        import numpy as np
        rng = np.random.RandomState(42)
        barrier_steps = rng.uniform(-2, 1, size=nb_dates)
        barrier_path_upper = [125]  # Initial barrier
        for step in barrier_steps:
            barrier_path_upper.append(barrier_path_upper[-1] + step)
    elif product == 'doublemovingbarrierdispersioncall':
        # DoubleStepBarrierDispersionCall: double moving barriers
        import numpy as np
        rng = np.random.RandomState(42)

        # Lower barrier
        lower_steps = rng.uniform(-1, 2, size=nb_dates)
        barrier_path_lower = [85]  # Initial barrier
        for step in lower_steps:
            barrier_path_lower.append(barrier_path_lower[-1] + step)

        # Upper barrier
        upper_steps = rng.uniform(-2, 1, size=nb_dates)
        barrier_path_upper = [115]  # Initial barrier
        for step in upper_steps:
            barrier_path_upper.append(barrier_path_upper[-1] + step)

    # Convert path to list format for JSON
    # Shape: (nb_stocks, nb_dates+1)
    path_list = selected_path[0].tolist()

    # Game metadata
    game_info = {
        'name': game['name'],
        'description': game['description'],
        'nb_stocks': game['nb_stocks'],
        'nb_dates': nb_dates,
        'strike': 100,  # K=100 for all games
        'maturity': float(model.maturity),
        'dt': float(model.dt),
        'difficulty': game['difficulty']
    }

    if 'barrier' in game:
        game_info['barrier'] = game['barrier']
    if 'barrier_down' in game:
        game_info['barrier_down'] = game['barrier_down']
    if 'barrier_up' in game:
        game_info['barrier_up'] = game['barrier_up']
    if 'barrier_type' in game:
        game_info['barrier_type'] = game['barrier_type']

    response = {
        'game_id': f"{product}_{path_idx}",
        'path': path_list,
        'machine_decisions': machine_decisions,
        'machine_exercise_date': machine_exercise_date,
        'payoffs_timeline': payoffs_timeline,
        'game_info': game_info
    }

    # Add barrier paths if they exist (for moving barrier games)
    if barrier_path_upper is not None:
        response['barrier_path_upper'] = barrier_path_upper
    if barrier_path_lower is not None:
        response['barrier_path_lower'] = barrier_path_lower

    return jsonify(response)


@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information."""
    return jsonify({
        'message': 'Optimal Stopping Game API',
        'version': '2.0.0',
        'games_available': len(GAME_DATA),
        'endpoints': {
            'health': '/api/health',
            'game_info': '/api/game/info',
            'start_game': '/api/game/start?product={game_id}'
        },
        'frontend': 'Please run the frontend application on port 3000',
        'status': 'running'
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'games_loaded': list(GAME_DATA.keys()),
        'total_games': len(GAME_DATA)
    })


# Load data on startup (must be at module level for gunicorn)
load_game_data()


if __name__ == '__main__':
    # Start server
    print("\nStarting API server on http://localhost:5000")
    print("Endpoints:")
    print("  GET /api/health")
    print("  GET /api/game/info")
    print("  GET /api/game/start?product={game_id}")
    print(f"\nAvailable games: {list(GAME_DATA.keys())}")
    print("\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
