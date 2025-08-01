#!/usr/bin/env python3
"""
Test MindsDB MCP tools directly using mcp client
"""

import asyncio
import json
from mcp.client.sse import sse_client
from mcp import ClientSession
from datetime import timedelta

async def test_mindsdb_mcp_tools():
    """Test MindsDB MCP tools via SSE connection"""
    print("Testing MindsDB MCP Tools via SSE")
    print("=" * 50)
    
    # Test SSE connection to MindsDB MCP
    try:
        async with sse_client("http://localhost:47337/sse") as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
                # Initialize the connection
                print("🔗 Initializing MCP session...")
                await session.initialize()
                print("✅ MCP session initialized successfully!")
                
                # List available tools
                print("\n📋 Listing available tools...")
                tools_result = await session.list_tools()
                
                if tools_result.tools:
                    print(f"✅ Found {len(tools_result.tools)} tools:")
                    for tool in tools_result.tools:
                        print(f"  - {tool.name}: {tool.description}")
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            props = tool.inputSchema.get('properties', {})
                            if props:
                                print(f"    Parameters: {list(props.keys())}")
                else:
                    print("❌ No tools found")
                    return
                
                # Test list_databases tool
                print("\n🗄️  Testing list_databases tool...")
                try:
                    db_result = await session.call_tool("list_databases", {})
                    print("✅ list_databases result:")
                    for content in db_result.content:
                        if hasattr(content, 'text'):
                            print(f"  {content.text}")
                        else:
                            print(f"  {content}")
                except Exception as e:
                    print(f"❌ list_databases failed: {e}")
                
                # Test query tool with simple query
                print("\n🔍 Testing query tool...")
                try:
                    query_result = await session.call_tool("query", {
                        "query": "SHOW DATABASES;"
                    })
                    print("✅ query result:")
                    for content in query_result.content:
                        if hasattr(content, 'text'):
                            print(f"  {content.text}")
                        else:
                            print(f"  {content}")
                except Exception as e:
                    print(f"❌ query failed: {e}")
                
                # Test query with actual data
                print("\n📊 Testing query on htinfo_db...")
                try:
                    tables_result = await session.call_tool("query", {
                        "query": "SHOW TABLES FROM htinfo_db;"
                    })
                    print("✅ htinfo_db tables:")
                    for content in tables_result.content:
                        if hasattr(content, 'text'):
                            print(f"  {content.text}")
                        else:
                            print(f"  {content}")
                except Exception as e:
                    print(f"❌ htinfo_db query failed: {e}")
                
    except Exception as e:
        print(f"❌ MCP connection failed: {e}")
        print("\nTrying alternative approaches...")
        
        # Try direct HTTP approach if SSE fails
        try:
            import requests
            
            print("\n🌐 Testing HTTP-based MCP interaction...")
            response = requests.post(
                "http://localhost:47337/api/mcp",
                json={
                    "method": "tools/list",
                    "params": {}
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ HTTP MCP endpoint working:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"❌ HTTP MCP failed: {response.status_code}")
                
        except Exception as http_e:
            print(f"❌ HTTP approach also failed: {http_e}")

async def main():
    print("MindsDB MCP Tools Test")
    print("=" * 50)
    await test_mindsdb_mcp_tools()
    
    print("\n" + "=" * 50)
    print("Summary & Next Steps:")
    print("- If tools are found: Use the exact tool names in deer-flow")
    print("- If connection works: Use http://localhost:47337/sse in frontend")
    print("- If no tools: MindsDB MCP may need additional configuration")

if __name__ == "__main__":
    asyncio.run(main())