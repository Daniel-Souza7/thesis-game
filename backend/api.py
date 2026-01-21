"""
Flask API server for the thesis game.

Endpoints:
- GET /api/game/start?product={game_id} - Start a new game
- GET /api/game/info - Get game parameters
"""

import sys
import os

# Add parent directory to path for backend module imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request
from flask_cors import CORS
import numpy as np
import pickle
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Paths (relative to this script's location)
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
PATHS_DIR = os.path.join(DATA_DIR, 'paths')
MODELS_DIR = os.path.join(DATA_DIR, 'trained_models')

# Global storage for loaded data (lazy loaded on-demand)
GAME_DATA = {}
LOADED_MODELS_CACHE = {}  # Cache for loaded models (max 1 at a time to save memory)
MAX_CACHED_MODELS = 1

# Game configurations - ALL 9 GAMES with lazy loading
# Only 1 model loaded in memory at a time to stay within 512MB
GAME_CONFIGS = [
    # MEDIUM
    {
        'id': 'upandoutcall',
        'name': 'UpAndOutCall',
        'description': '1 stock, upper barrier at 120',
        'nb_stocks': 1,
        'difficulty': 'Medium',
        'barrier': 120,
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

# Default game to pre-load at startup for instant first click
DEFAULT_GAME = 'upandoutcall'  # Smallest model (13MB), Medium difficulty


def load_game_metadata():
    """Load only game metadata on server startup (no models or paths)."""
    print("Loading game metadata (models will be loaded on-demand)...")

    for config in GAME_CONFIGS:
        game_id = config['id']

        # Store only metadata, no models or paths yet
        GAME_DATA[game_id] = {
            'name': config['name'],
            'description': config['description'],
            'nb_stocks': config['nb_stocks'],
            'difficulty': config['difficulty'],
            'barrier_type': config['barrier_type'],
            'loaded': False  # Track if model is loaded
        }

        # Add barrier information
        if 'barrier' in config:
            GAME_DATA[game_id]['barrier'] = config['barrier']
        if 'barrier_up' in config:
            GAME_DATA[game_id]['barrier_up'] = config['barrier_up']
        if 'barrier_down' in config:
            GAME_DATA[game_id]['barrier_down'] = config['barrier_down']

    print(f"Loaded metadata for {len(GAME_DATA)} games")


def load_model_for_game(game_id):
    """
    Lazy load a specific game's model and test paths.
    Uses a cache to keep at most MAX_CACHED_MODELS in memory.
    """
    # If already loaded in cache, return
    if game_id in LOADED_MODELS_CACHE:
        print(f"Using cached model for {game_id}")
        return LOADED_MODELS_CACHE[game_id]

    print(f"Loading model for {game_id}...")

    # Get config for this game
    config = None
    for c in GAME_CONFIGS:
        if c['id'] == game_id:
            config = c
            break

    if config is None:
        raise ValueError(f"Unknown game_id: {game_id}")

    # Load test paths for this stock count (only if not already loaded)
    nb_stocks = config['nb_stocks']
    test_paths = None

    try:
        test_data = np.load(os.path.join(PATHS_DIR, f'test_{nb_stocks}stock.npz'))
        test_paths = test_data['paths']
        print(f"  ✓ Loaded test paths for {nb_stocks} stock(s)")
    except Exception as e:
        print(f"  ✗ Failed to load test paths: {e}")
        raise

    # Load trained model
    try:
        model_file = os.path.join(MODELS_DIR, f"{game_id}.pkl")
        with open(model_file, 'rb') as f:
            model_data = pickle.load(f)
        print(f"  ✓ Loaded model for {game_id}")
    except Exception as e:
        print(f"  ✗ Failed to load model: {e}")
        raise

    # Cache management: remove oldest if cache is full
    if len(LOADED_MODELS_CACHE) >= MAX_CACHED_MODELS:
        oldest_key = next(iter(LOADED_MODELS_CACHE))
        print(f"  Cache full, removing {oldest_key}")
        del LOADED_MODELS_CACHE[oldest_key]

    # Store in cache (support both 'rt' and 'srlsm' keys for backwards compatibility)
    rt_model = model_data.get('rt', model_data.get('srlsm'))
    model_cache = {
        'rt': rt_model,
        'model': model_data['model'],
        'payoff': model_data['payoff'],
        'test_paths': test_paths,
        'price': model_data['price'],
        'avg_exercise_time': model_data['avg_exercise_time']
    }

    LOADED_MODELS_CACHE[game_id] = model_cache
    GAME_DATA[game_id]['loaded'] = True

    return model_cache


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
            'strike': 100  # K=100 for all games
        }

        # Add barrier information if available
        if 'barrier' in data:
            games[key]['barrier'] = data['barrier']
        if 'barrier_down' in data:
            games[key]['barrier_down'] = data['barrier_down']
        if 'barrier_up' in data:
            games[key]['barrier_up'] = data['barrier_up']

        # If model is loaded in cache, include additional details
        if key in LOADED_MODELS_CACHE:
            model_cache = LOADED_MODELS_CACHE[key]
            games[key]['maturity'] = model_cache['model'].maturity
            games[key]['nb_dates'] = model_cache['model'].nb_dates
            games[key]['price'] = float(model_cache['price'])
            games[key]['avg_exercise_time'] = float(model_cache['avg_exercise_time'])

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

    # Lazy load the model for this game
    try:
        model_cache = load_model_for_game(product)
    except Exception as e:
        return jsonify({'error': f'Failed to load game model: {str(e)}'}), 500

    # Get metadata
    game_metadata = GAME_DATA[product]

    # Select a random test path
    test_paths = model_cache['test_paths']
    path_idx = random.randint(0, len(test_paths) - 1)
    selected_path = test_paths[path_idx:path_idx+1]  # Shape: (1, nb_stocks, nb_dates+1)

    # Predict machine exercise decision
    rt = model_cache['rt']
    payoff = model_cache['payoff']
    model = model_cache['model']

    exercise_dates = rt.predict_exercise_decisions(selected_path)
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
        'name': game_metadata['name'],
        'description': game_metadata['description'],
        'nb_stocks': game_metadata['nb_stocks'],
        'nb_dates': nb_dates,
        'strike': 100,  # K=100 for all games
        'maturity': float(model.maturity),
        'dt': float(model.dt),
        'difficulty': game_metadata['difficulty']
    }

    if 'barrier' in game_metadata:
        game_info['barrier'] = game_metadata['barrier']
    if 'barrier_down' in game_metadata:
        game_info['barrier_down'] = game_metadata['barrier_down']
    if 'barrier_up' in game_metadata:
        game_info['barrier_up'] = game_metadata['barrier_up']
    if 'barrier_type' in game_metadata:
        game_info['barrier_type'] = game_metadata['barrier_type']

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


@app.route('/api/keepalive', methods=['GET'])
def keepalive():
    """
    Keep-alive endpoint to prevent cold starts on free tier hosting.

    Use a cron service (e.g., cron-job.org, UptimeRobot) to ping this endpoint
    every 14 minutes to keep the service warm.

    Free tier services spin down after 15 minutes of inactivity.
    """
    return jsonify({
        'status': 'alive',
        'timestamp': int(np.datetime64('now').astype('int64') / 1e9),
        'cached_game': list(LOADED_MODELS_CACHE.keys())[0] if LOADED_MODELS_CACHE else None
    })


# Load only metadata on startup (models loaded on-demand to save memory)
load_game_metadata()

# Pre-load default game for instant first click
try:
    print(f"\nPre-loading default game '{DEFAULT_GAME}' for instant first click...")
    load_model_for_game(DEFAULT_GAME)
    print(f"✓ Default game ready!\n")
except Exception as e:
    print(f"✗ Warning: Failed to pre-load default game: {e}\n")


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
