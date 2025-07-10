#!/usr/bin/env python3
"""
Token Management Toggle Script

This script allows you to easily enable/disable token management for comparison testing.
It directly modifies the conf.yaml file to toggle the 'enabled' setting.

Usage:
    python scripts/toggle_token_management.py [on|off|status]
    
    on      - Enable token management
    off     - Disable token management  
    status  - Show current status
    
If no argument is provided, it will show the current status and prompt for action.
"""

import sys
import yaml
from pathlib import Path

def get_config_path():
    """Get the path to conf.yaml"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root / "conf.yaml"

def load_config():
    """Load the current configuration"""
    config_path = get_config_path()
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f), config_path
    except Exception as e:
        print(f"❌ Error loading config from {config_path}: {e}")
        sys.exit(1)

def save_config(config, config_path):
    """Save the configuration back to file"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"❌ Error saving config to {config_path}: {e}")
        return False

def get_current_status(config):
    """Get the current token management status"""
    token_mgmt = config.get("TOKEN_MANAGEMENT", {})
    return token_mgmt.get("enabled", False)

def toggle_token_management(config, enable):
    """Toggle token management on/off"""
    if "TOKEN_MANAGEMENT" not in config:
        config["TOKEN_MANAGEMENT"] = {}
    
    config["TOKEN_MANAGEMENT"]["enabled"] = enable
    return config

def show_status(config):
    """Show current token management status and configuration"""
    token_mgmt = config.get("TOKEN_MANAGEMENT", {})
    enabled = token_mgmt.get("enabled", False)
    
    print("🔍 Token Management Status")
    print("=" * 50)
    print(f"Status: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
    
    if enabled:
        print(f"Safety Margin: {token_mgmt.get('safety_margin', 'N/A')}")
        print(f"Model Limits: {len(token_mgmt.get('model_limits', {}))} models configured")
        print(f"Node Strategies: {len(token_mgmt.get('trimming_strategies', {}))} nodes configured")
    
    print("=" * 50)

def main():
    """Main function"""
    config, config_path = load_config()
    
    if len(sys.argv) == 1:
        # No arguments - show status and prompt
        show_status(config)
        print("\nOptions:")
        print("  python scripts/toggle_token_management.py on      - Enable token management")
        print("  python scripts/toggle_token_management.py off     - Disable token management")
        print("  python scripts/toggle_token_management.py status  - Show status only")
        return
    
    command = sys.argv[1].lower()
    current_status = get_current_status(config)
    
    if command == "status":
        show_status(config)
        return
    
    elif command == "on":
        if current_status:
            print("✅ Token management is already enabled")
        else:
            config = toggle_token_management(config, True)
            if save_config(config, config_path):
                print("✅ Token management enabled successfully")
                print("💡 Restart the server to apply changes")
            else:
                sys.exit(1)
    
    elif command == "off":
        if not current_status:
            print("❌ Token management is already disabled")
        else:
            config = toggle_token_management(config, False)
            if save_config(config, config_path):
                print("❌ Token management disabled successfully")
                print("💡 Restart the server to apply changes")
                print("⚠️  Warning: Disabling token management may cause token limit errors with large contexts")
            else:
                sys.exit(1)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: on, off, status")
        sys.exit(1)

if __name__ == "__main__":
    main()