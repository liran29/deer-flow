#!/bin/bash

# Start both of DeerFlow's backend and web UI server.
# If the user presses Ctrl+C, kill them both.

# Parse options
DEBUG_LOG=""
DEV_MODE=""
TOKEN_MGMT_ACTION=""

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
    --token-mgmt-on|--enable-token-mgmt)
      TOKEN_MGMT_ACTION="on"
      ;;
    --token-mgmt-off|--disable-token-mgmt)
      TOKEN_MGMT_ACTION="off"
      ;;
    --help|-h)
      echo "DeerFlow Bootstrap Script with Logging and Token Management"
      echo ""
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Development Options:"
      echo "  -d, --dev               Start in development mode"
      echo ""
      echo "Logging Options:"
      echo "  --debug-log             Enable debug-level file logging"
      echo "  --log                   Enable info-level file logging"
      echo ""
      echo "Token Management Options:"
      echo "  --token-mgmt-on         Enable token management before starting"
      echo "  --token-mgmt-off        Disable token management before starting"
      echo ""
      echo "Examples:"
      echo "  $0 -d                                    # Development mode"
      echo "  $0 -d --debug-log                       # Development + debug logging"
      echo "  $0 -d --debug-log --token-mgmt-off      # Development + logging + token mgmt disabled"
      echo "  $0 --token-mgmt-on                      # Production with token management enabled"
      echo ""
      exit 0
      ;;
    *)
      # Unknown option - ignore for backwards compatibility
      ;;
  esac
done

# Handle token management configuration
if [ -n "$TOKEN_MGMT_ACTION" ]; then
  echo "🔧 Configuring token management..."
  python scripts/toggle_token_management.py $TOKEN_MGMT_ACTION
  if [ $? -ne 0 ]; then
    echo "❌ Failed to configure token management"
    exit 1
  fi
  echo ""
fi

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
