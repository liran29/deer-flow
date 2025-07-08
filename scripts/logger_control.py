#!/usr/bin/env python3
"""
Control logger file output for deer-flow.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger_config import LoggerConfig, enable_debug_file_logging, disable_file_logging


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Control logger file output')
    parser.add_argument('action', choices=['enable', 'disable', 'status'], 
                       help='Action to perform')
    parser.add_argument('--debug', '-d', action='store_true',
                       help='Enable debug level logging')
    parser.add_argument('--filename', '-f', 
                       help='Custom log filename')
    
    args = parser.parse_args()
    
    if args.action == 'enable':
        if args.debug:
            log_path = enable_debug_file_logging(args.filename)
            print(f"✅ Debug file logging enabled")
        else:
            log_path = LoggerConfig.enable_file_logging(
                log_filename=args.filename
            )
            print(f"✅ File logging enabled")
        print(f"📄 Log file: {log_path}")
        print(f"💡 All logger output will be saved to this file")
        
    elif args.action == 'disable':
        disable_file_logging()
        print("🛑 File logging disabled")
        
    elif args.action == 'status':
        if LoggerConfig.is_file_logging_enabled():
            print(f"✅ File logging is enabled")
            print(f"📄 Log file: {LoggerConfig.get_log_file_path()}")
        else:
            print("🛑 File logging is disabled")


if __name__ == "__main__":
    main()