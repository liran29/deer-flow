#!/usr/bin/env python3
"""
Test Token Management Toggle

This script tests whether the token management enable/disable switch works correctly.
It creates a scenario where token management would normally be triggered and verifies
the behavior with and without token management enabled.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.token_manager import TokenManager
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def create_large_message_list():
    """Create a list of messages that would exceed token limits"""
    messages = []
    
    # Add system message
    messages.append(SystemMessage(content="You are a helpful research assistant. " * 100))
    
    # Add user query
    messages.append(HumanMessage(content="Analyze large language models in healthcare, finance, and education."))
    
    # Add many tool results (simulating multiple search results)
    for i in range(25):
        # Simulate tool results with large content
        tool_result = f"Search result {i+1}:\n" + "This is a very long search result content. " * 200
        messages.append(AIMessage(content=f"Let me search for more information..."))
        messages.append(HumanMessage(content=tool_result))
    
    return messages

def test_token_management_status():
    """Test the current token management status"""
    print("🧪 Testing Token Management Toggle")
    print("=" * 60)
    
    # Initialize TokenManager
    token_manager = TokenManager()
    is_enabled = token_manager.token_management.get("enabled", False)
    
    print(f"Current Status: {'✅ ENABLED' if is_enabled else '❌ DISABLED'}")
    
    # Create test messages
    messages = create_large_message_list()
    original_count = len(messages)
    
    print(f"Original Messages: {original_count}")
    
    # Apply token management
    try:
        trimmed_messages = token_manager.trim_messages_for_node(
            messages, "deepseek-chat", "researcher"
        )
        trimmed_count = len(trimmed_messages)
        
        print(f"After Processing: {trimmed_count} messages")
        
        if is_enabled:
            if trimmed_count < original_count:
                print("✅ Token management is working - messages were trimmed")
                print(f"   Removed: {original_count - trimmed_count} messages")
            else:
                print("ℹ️  Token management is enabled but no trimming was needed")
                print("   (Messages were within limits)")
        else:
            if trimmed_count == original_count:
                print("✅ Token management is disabled - no trimming occurred")
            else:
                print("❌ Unexpected: Messages were trimmed despite being disabled")
        
        # Show token limit info
        model_limit = token_manager.get_model_limit("deepseek-chat")
        researcher_config = token_manager.get_trimming_strategy("researcher")
        max_allowed = researcher_config.get("max_tokens", model_limit)
        
        print(f"Model Limit: {model_limit:,} tokens")
        print(f"Node Limit: {max_allowed:,} tokens")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    test_token_management_status()
    
    print("\n💡 Usage:")
    print("1. Run this script to see current behavior")
    print("2. Use 'python scripts/toggle_token_management.py off' to disable")
    print("3. Run this script again to see disabled behavior")
    print("4. Use 'python scripts/toggle_token_management.py on' to re-enable")

if __name__ == "__main__":
    main()