#!/usr/bin/env python3
"""
Enable debug logging for token management analysis.
This will save all relevant logs to a file for debugging.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.debug_logger import start_debug_logging, stop_debug_logging


def main():
    """Main function to toggle debug logging."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Toggle debug logging for token management')
    parser.add_argument('action', choices=['start', 'stop', 'status'], 
                       help='Action to perform')
    parser.add_argument('--session', '-s', default='researcher_debug',
                       help='Session name for the log file')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        logger = start_debug_logging(session_name=args.session)
        print(f"✅ Debug logging started")
        print(f"📄 Log file: {logger.log_path}")
        print(f"🔍 Monitoring loggers:")
        for name in ['src.graph.nodes', 'src.utils.token_manager', 
                    'src.utils.token_counter', 'httpx']:
            print(f"   - {name}")
        
        # Save the session info for later
        with open("logs/debug/.current_session", "w") as f:
            f.write(logger.log_path)
            
    elif args.action == 'stop':
        stop_debug_logging()
        print("🛑 Debug logging stopped")
        
        # Remove session info
        if os.path.exists("logs/debug/.current_session"):
            os.remove("logs/debug/.current_session")
            
    elif args.action == 'status':
        if os.path.exists("logs/debug/.current_session"):
            with open("logs/debug/.current_session", "r") as f:
                log_path = f.read().strip()
            print(f"✅ Debug logging is active")
            print(f"📄 Current log file: {log_path}")
        else:
            print("🛑 Debug logging is not active")


if __name__ == "__main__":
    main()