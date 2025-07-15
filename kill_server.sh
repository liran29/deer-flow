#!/bin/bash

# Kill processes running on port 8000 and 3000
# Based on bootstrap.sh process management

echo "Checking for processes on port 8000 (DeerFlow backend)..."
SERVER_PID=$(lsof -ti:8000)
if [ ! -z "$SERVER_PID" ]; then
    echo "Killing server process $SERVER_PID"
    kill -9 $SERVER_PID
    echo "Server process killed"
else
    echo "No server process found on port 8000"
fi

echo "Checking for processes on port 3000 (DeerFlow web UI)..."
WEB_PID=$(lsof -ti:3000)
if [ ! -z "$WEB_PID" ]; then
    echo "Killing web process $WEB_PID"
    kill -9 $WEB_PID
    echo "Web process killed"
else
    echo "No web process found on port 3000"
fi

# Also check for any python processes that might be running server.py
echo "Checking for any remaining server.py processes..."
SERVER_PYTHON_PID=$(ps aux | grep "server.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$SERVER_PYTHON_PID" ]; then
    echo "Killing server.py process $SERVER_PYTHON_PID"
    kill -9 $SERVER_PYTHON_PID
    echo "server.py process killed"
else
    echo "No server.py processes found"
fi

echo "All processes cleaned up!"