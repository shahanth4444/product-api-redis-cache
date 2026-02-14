#!/bin/bash
# Test script to check application startup

echo "=== Testing Application Startup ==="
cd /app

echo "=== Python Version ==="
python --version

echo "=== Installed Packages ==="
pip list | grep -E "(fastapi|uvicorn|redis|sqlalchemy|pydantic)"

echo "=== Testing Import ==="
python -c "from src.main import app; print('Import successful!')"

echo "=== Starting Application (5 seconds) ==="
timeout 5 python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 || true

echo "=== Test Complete ==="
