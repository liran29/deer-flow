#!/usr/bin/env python3
"""
Test MindsDB MCP streamable_http transport support
"""

import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from datetime import timedelta

async def test_mindsdb_streamable_http():
    """Test MindsDB MCP via streamable_http transport"""
    print("Testing MindsDB MCP via Streamable HTTP")
    print("=" * 50)
    
    # Test different possible streamable_http endpoints
    test_urls = [
        "http://localhost:47337",           # Standard MCP endpoint
        "http://localhost:47337/mcp",       # MCP-specific endpoint
        "http://localhost:47334/mcp",       # HTTP API port with MCP
        "http://localhost:47335",           # Alternative MCP port
    ]
    
    for url in test_urls:
        print(f"\n🔗 Testing streamable_http: {url}")
        try:
            async with streamablehttp_client(url) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=10)) as session:
                    # Initialize the connection
                    print("  ✅ Connection initialized")
                    await session.initialize()
                    print("  ✅ Session initialized")
                    
                    # List available tools
                    tools_result = await session.list_tools()
                    print(f"  ✅ Found {len(tools_result.tools)} tools:")
                    for tool in tools_result.tools:
                        print(f"    - {tool.name}")
                    
                    # Quick test query
                    if tools_result.tools:
                        db_result = await session.call_tool("list_databases", {})
                        print(f"  ✅ Tool call successful")
                        return True
                        
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    return False

async def main():
    print("MindsDB Streamable HTTP Transport Test")
    print("=" * 50)
    
    success = await test_mindsdb_streamable_http()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ MindsDB supports streamable_http transport!")
        print("You can use either:")
        print("- SSE: http://localhost:47337/sse")
        print("- Streamable HTTP: [working endpoint from above]")
    else:
        print("❌ MindsDB streamable_http not working")
        print("Stick with SSE: http://localhost:47337/sse")

if __name__ == "__main__":
    asyncio.run(main())