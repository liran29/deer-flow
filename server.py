# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Server script for running the DeerFlow API.
"""

import argparse
import logging
import os
import signal
import sys
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def handle_shutdown(signum, frame):
    """Handle graceful shutdown on SIGTERM/SIGINT"""
    logger.info("Received shutdown signal. Starting graceful shutdown...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the DeerFlow API server")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (default: True except on Windows)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the server to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)",
    )
    parser.add_argument(
        "--log-to-file",
        action="store_true",
        help="Enable logging to file",
    )
    parser.add_argument(
        "--debug-log-to-file",
        action="store_true",
        help="Enable debug-level logging to file",
    )

    args = parser.parse_args()
    
    # Enable file logging if requested
    if args.log_to_file or args.debug_log_to_file:
        from src.utils.logger_config import enable_debug_file_logging, enable_file_logging
        
        if args.debug_log_to_file:
            log_path = enable_debug_file_logging()
            logger.info(f"✅ Debug file logging enabled: {log_path}")
            # Set environment variable so app startup can re-enable after uvicorn
            os.environ["DEER_FLOW_DEBUG_LOG_TO_FILE"] = "true"
        else:
            log_path = enable_file_logging()
            logger.info(f"✅ File logging enabled: {log_path}")
            # Set environment variable so app startup can re-enable after uvicorn
            os.environ["DEER_FLOW_LOG_TO_FILE"] = "true"

    # Determine reload setting
    reload = False
    if args.reload:
        reload = True

    try:
        logger.info(f"Starting DeerFlow API server on {args.host}:{args.port}")
        
        # Configure uvicorn to preserve our file logging
        log_config = None
        if args.log_to_file or args.debug_log_to_file:
            # Create custom uvicorn log config that preserves our file handler
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "root": {
                    "level": args.log_level.upper(),
                    "handlers": ["default"],
                    "propagate": True,
                },
                "loggers": {
                    "uvicorn": {"level": args.log_level.upper(), "propagate": True},
                    "uvicorn.error": {"level": args.log_level.upper(), "propagate": True},
                    "uvicorn.access": {"level": "WARNING", "propagate": True},
                },
            }
        
        uvicorn.run(
            "src.server:app",
            host=args.host,
            port=args.port,
            reload=reload,
            log_level=args.log_level,
            log_config=log_config,
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)
