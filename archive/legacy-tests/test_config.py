#!/usr/bin/env python3
"""
Test script to debug configuration loading issues
"""

import os
import sys
from dotenv import load_dotenv

print("=== Configuration Test ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

# Load environment files in the same order as main.py
print("\n=== Loading Environment Files ===")
try:
    load_dotenv(".env.local")
    print("✓ Loaded .env.local")
except Exception as e:
    print(f"✗ Failed to load .env.local: {e}")

try:
    load_dotenv("../.env.local")
    print("✓ Loaded ../.env.local")
except Exception as e:
    print(f"✗ Failed to load ../.env.local: {e}")

# Check environment variables
print("\n=== Environment Variables ===")
cors_origins = os.getenv("CORS_ORIGINS")
print(f"CORS_ORIGINS from env: {cors_origins}")
print(f"Type: {type(cors_origins)}")

# Try to import settings
print("\n=== Settings Import Test ===")
try:
    from app.core.config import Settings
    settings = Settings()
    print("✓ Settings imported successfully")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print(f"Type: {type(settings.CORS_ORIGINS)}")
except Exception as e:
    print(f"✗ Failed to import settings: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")