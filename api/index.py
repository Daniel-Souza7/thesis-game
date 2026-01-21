"""
Vercel serverless function wrapper for Flask API.

This file adapts the Flask app to work as a Vercel serverless function.
"""

import sys
import os

# Add backend directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if os.path.dirname(current_dir) not in sys.path:
    sys.path.insert(0, os.path.dirname(current_dir))

# Import the Flask app from backend
from backend.api import app

# Export for Vercel
# Vercel will call this as a WSGI application
def handler(request, context):
    """Vercel serverless function handler."""
    return app(request, context)

# For compatibility with Vercel's Python runtime
# This makes the Flask app available as 'app' at the module level
__all__ = ['app', 'handler']
