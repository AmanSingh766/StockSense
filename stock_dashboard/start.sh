#!/bin/bash
echo "Starting StockSense Dashboard..."
cd backend
pip install -r ../requirements.txt -q
python main.py
