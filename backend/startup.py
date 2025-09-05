#!/usr/bin/env python3
"""
Startup script to ensure all required directories exist before starting the application
"""
import os
import logging

def ensure_directories():
    """Create required directories if they don't exist"""
    directories = [
        "/tmp/documents",
        "/tmp/exports", 
        "logs",
        "data"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created/verified directory: {directory}")
        except Exception as e:
            print(f"✗ Failed to create directory {directory}: {e}")
    
    print("Directory setup complete")

if __name__ == "__main__":
    ensure_directories()