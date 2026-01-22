"""
Vercel serverless function wrapper for Flask API.

This file adapts the Flask app to work as a Vercel serverless function.
Vercel automatically detects the 'app' variable as a WSGI application.
"""

import sys
import os

# Add project root to path so 'backend' package can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the Flask app from backend
# Vercel will automatically use this as a WSGI application
from backend.api import app
