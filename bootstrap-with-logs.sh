#!/bin/bash

# Start both of DeerFlow's backend and web UI server.
# If the user presses Ctrl+C, kill them both.

# Parse options
DEBUG_LOG=""
DEV_MODE=""

for arg in "$@"; do
  case $arg in
    --dev|-d|dev|development)
      DEV_MODE="true"
      ;;
    --debug-log|--log-debug)
      DEBUG_LOG="--debug-log-to-file"
      ;;
    --log|--log-file)
      DEBUG_LOG="--log-to-file"
      ;;
    *)
      # Unknown option
      ;;
  esac
done

if [ "$DEV_MODE" = "true" ]; then
  echo -e "Starting DeerFlow in [DEVELOPMENT] mode..."
  if [ -n "$DEBUG_LOG" ]; then
    echo -e "📄 Debug logging enabled - logs will be saved to file\n"
    uv run server.py --reload $DEBUG_LOG & SERVER_PID=$!
  else
    echo ""
    uv run server.py --reload & SERVER_PID=$!
  fi
  cd web && pnpm dev & WEB_PID=$!
  trap "kill $SERVER_PID $WEB_PID" SIGINT SIGTERM
  wait
else
  echo -e "Starting DeerFlow in [PRODUCTION] mode..."
  if [ -n "$DEBUG_LOG" ]; then
    echo -e "📄 Debug logging enabled - logs will be saved to file\n"
    uv run server.py $DEBUG_LOG & SERVER_PID=$!
  else
    echo ""
    uv run server.py & SERVER_PID=$!
  fi
  cd web && pnpm start & WEB_PID=$!
  trap "kill $SERVER_PID $WEB_PID" SIGINT SIGTERM
  wait
fi
