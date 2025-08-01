#!/usr/bin/env python3
"""
Test script to check if MindsDB MCP server is working properly
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

async def test_mindsdb_http_api():
    """Test MindsDB HTTP API first"""
    print("=" * 60)
    print("1. Testing MindsDB HTTP API")
    print("=" * 60)
    
    try:
        import requests
        
        # Test basic connection
        response = requests.get("http://localhost:47334", timeout=5)
        print(f"✓ MindsDB HTTP API accessible: {response.status_code}")
        
        # Test SQL query endpoint
        test_query = {"query": "SHOW DATABASES;"}
        response = requests.post(
            "http://localhost:47334/api/sql/query",
            headers={"Content-Type": "application/json"},
            json=test_query,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ SQL API working: Found {len(result.get('data', []))} databases")
            print(f"  Databases: {[row[0] for row in result.get('data', [])]}")
        else:
            print(f"✗ SQL API failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"✗ MindsDB HTTP API test failed: {e}")
        return False
    
    return True

def test_mindsdb_mcp_ports():
    """Test MindsDB MCP ports"""
    print("\n" + "=" * 60)
    print("2. Testing MindsDB MCP Ports")
    print("=" * 60)
    
    import socket
    
    ports_to_test = [47335, 47336, 47337]  # Common MCP ports
    
    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"✓ Port {port} is open")
            else:
                print(f"✗ Port {port} is closed")
        except Exception as e:
            print(f"✗ Port {port} test failed: {e}")

async def test_mcp_stdio_connection():
    """Test MCP stdio connection methods"""
    print("\n" + "=" * 60)
    print("3. Testing MCP stdio connections")
    print("=" * 60)
    
    # Test various possible MindsDB MCP commands
    possible_commands = [
        ["python", "-m", "minds_mcp"],
        ["python", "-m", "mindsdb.mcp"],
        ["mindsdb", "--mcp"],
        ["mindsdb-mcp"],
        ["mcp-server-mindsdb"],
    ]
    
    for cmd in possible_commands:
        print(f"Testing command: {' '.join(cmd)}")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit to see if it starts
            time.sleep(2)
            
            # Check if process is still running
            if proc.poll() is None:
                print(f"✓ Command started successfully (PID: {proc.pid})")
                proc.terminate()
                proc.wait(timeout=5)
            else:
                stdout, stderr = proc.communicate()
                print(f"✗ Command failed:")
                if stdout:
                    print(f"  stdout: {stdout[:200]}")
                if stderr:
                    print(f"  stderr: {stderr[:200]}")
                    
        except FileNotFoundError:
            print(f"✗ Command not found: {cmd[0]}")
        except Exception as e:
            print(f"✗ Command error: {e}")
        
        print()

async def test_mcp_sse_connection():
    """Test MCP SSE connection"""
    print("\n" + "=" * 60)  
    print("4. Testing MCP SSE connections")
    print("=" * 60)
    
    import aiohttp
    
    # Test various possible MindsDB MCP SSE endpoints
    possible_urls = [
        "http://localhost:47335/sse",
        "http://localhost:47336/sse", 
        "http://localhost:47337/sse",
        "http://localhost:47334/mcp/sse",
        "http://localhost:47334/api/mcp/sse",
    ]
    
    for url in possible_urls:
        print(f"Testing SSE endpoint: {url}")
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"✓ SSE endpoint accessible: {response.status}")
                        content_type = response.headers.get('content-type', '')
                        print(f"  Content-Type: {content_type}")
                    else:
                        print(f"✗ SSE endpoint failed: {response.status}")
                        
        except Exception as e:
            print(f"✗ SSE connection failed: {e}")
        
        print()

def check_mindsdb_installation():
    """Check MindsDB installation and MCP support"""
    print("\n" + "=" * 60)
    print("5. Checking MindsDB Installation & MCP Support")
    print("=" * 60)
    
    try:
        # Check if MindsDB is installed
        result = subprocess.run(["python", "-c", "import mindsdb; print(mindsdb.__version__)"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ MindsDB Python package installed: v{result.stdout.strip()}")
        else:
            print("✗ MindsDB Python package not found")
            
    except Exception as e:
        print(f"✗ MindsDB installation check failed: {e}")
    
    # Check for MCP-related packages
    mcp_packages = ["mcp", "minds-mcp", "mindsdb-mcp"]
    for package in mcp_packages:
        try:
            result = subprocess.run(["python", "-c", f"import {package.replace('-', '_')}; print('OK')"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✓ {package} package available")
            else:
                print(f"✗ {package} package not found")
        except Exception as e:
            print(f"✗ {package} check failed: {e}")

def check_docker_mindsdb():
    """Check MindsDB Docker container"""
    print("\n" + "=" * 60)
    print("6. Checking MindsDB Docker Container")
    print("=" * 60)
    
    try:
        # Check if MindsDB container is running
        result = subprocess.run(["docker", "ps", "--filter", "name=mindsdb", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "mindsdb" in result.stdout:
            print("✓ MindsDB Docker container found:")
            print(result.stdout)
        else:
            print("✗ MindsDB Docker container not running")
            
        # Check Docker logs for MCP-related messages
        log_result = subprocess.run(["docker", "logs", "mindsdb", "--tail", "50"], 
                                  capture_output=True, text=True, timeout=10)
        if log_result.returncode == 0:
            logs = log_result.stdout.lower()
            if "mcp" in logs:
                print("✓ MCP mentioned in Docker logs")
                # Extract MCP-related lines
                mcp_lines = [line for line in log_result.stdout.split('\n') if 'mcp' in line.lower()]
                for line in mcp_lines[-5:]:  # Show last 5 MCP-related lines
                    print(f"  {line}")
            else:
                print("✗ No MCP mentions in Docker logs")
                
    except Exception as e:
        print(f"✗ Docker check failed: {e}")

async def main():
    """Main test function"""
    print("MindsDB MCP Server Test")
    print("=" * 60)
    print("This script will test various aspects of MindsDB MCP connectivity")
    print()
    
    # Run all tests
    await test_mindsdb_http_api()
    test_mindsdb_mcp_ports()
    await test_mcp_stdio_connection()
    await test_mcp_sse_connection()
    check_mindsdb_installation()
    check_docker_mindsdb()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print("Next steps based on results:")
    print("- If HTTP API works but MCP doesn't: MindsDB may not have MCP enabled")
    print("- If ports are closed: Check MindsDB configuration for MCP port")
    print("- If no MCP packages found: Install minds-mcp or configure MindsDB MCP")
    print("- If Docker container issues: Check MindsDB container configuration")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        sys.exit(1)