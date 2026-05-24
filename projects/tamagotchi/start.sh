#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Tamagotchi backend on port 5001..."
python3 server.py
