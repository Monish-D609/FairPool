"""
FairPool: Vercel Serverless Function Entrypoint
Exposes the FastAPI ASGI application for Vercel Python runtime (@vercel/python).
"""

import sys
import os

# Ensure project root is in Python sys.path so fairpool package can be imported in Vercel serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fairpool.api.app import app

# Vercel looks for 'app' ASGI callable
app = app
