#!/bin/bash

echo "🧪 Quick Application Test"
echo "========================"

# Set environment variables
export PORT=8080
export SECRET_KEY="test-secret-key"
export GROQ_API_KEY="test-key"
export GEMINI_API_KEY="test-key"

echo "1️⃣ Testing UV..."
uv --version
if [ $? -ne 0 ]; then
    echo "❌ UV not found"
    exit 1
fi

echo "2️⃣ Syncing dependencies..."
uv sync
if [ $? -ne 0 ]; then
    echo "❌ Failed to sync dependencies"
    exit 1
fi

echo "3️⃣ Testing import..."
uv run python -c "import sys; sys.path.insert(0, 'src'); from main import app; print('✅ Import successful'); print(f'Routes: {len(app.routes)}')"
if [ $? -ne 0 ]; then
    echo "❌ Import failed"
    exit 1
fi

echo "4️⃣ Testing server start (5 seconds)..."
timeout 5 uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server started successfully"
    kill $SERVER_PID 2>/dev/null
else
    echo "❌ Server failed to start"
    exit 1
fi

echo "========================"
echo "🎉 All tests passed!"
echo "✅ Application should work in Cloud Run"
