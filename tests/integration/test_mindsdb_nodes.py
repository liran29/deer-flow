#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for MindsDB nodes
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.runnables import RunnableConfig

# Mock the imports to avoid dependency issues
with patch("src.config.mindsdb_mcp.MindsDBMCPConfig"):
    with patch("src.tools.mindsdb_mcp.MindsDBMCPTool"):
        from src.graph.nodes_enhanced import database_query_node


@pytest.fixture
def mock_state():
    return {
        "research_topic": "Walmart sales analysis"
    }


@pytest.fixture
def mock_config():
    return RunnableConfig(configurable={})


@pytest.fixture
def mock_configurable():
    mock = MagicMock()
    mock.max_search_results = 7
    return mock


@pytest.fixture
def patch_config_from_runnable_config(mock_configurable):
    with patch(
        "src.graph.nodes_enhanced.Configuration.from_runnable_config",
        return_value=mock_configurable,
    ):
        yield


@pytest.fixture
def mock_mindsdb_tool():
    """Mock MindsDB tool with expected methods."""
    tool = MagicMock()
    
    # Mock get_available_databases (synchronous)
    tool.get_available_databases.return_value = ["htinfo_db", "ext_ref_db"]
    
    # Mock get_table_info (async)
    tool.get_table_info = AsyncMock()
    async def mock_get_table_info(database, table_name=None):
        if table_name:
            return {
                "success": True,
                "data": [
                    ["id", "int", "primary key"],
                    ["name", "varchar", "not null"],
                    ["price", "decimal", "nullable"]
                ]
            }
        else:
            if database == "htinfo_db":
                return {
                    "success": True,
                    "data": [["walmart_online_item"], ["walmart_orders"]]
                }
            elif database == "ext_ref_db":
                return {
                    "success": True,
                    "data": [["reference_data"]]
                }
            else:
                return {"success": False, "error": "Database not found"}
    
    tool.get_table_info.side_effect = mock_get_table_info
    
    # Mock query_database (async)
    tool.query_database = AsyncMock()
    async def mock_query_database(database, query):
        if "walmart_online_item" in query:
            return {
                "success": True,
                "columns": ["id", "product_name", "price"],
                "data": [
                    [1, "iPhone 15", 999.99],
                    [2, "Samsung TV", 599.99]
                ]
            }
        elif "walmart_orders" in query:
            return {
                "success": True,
                "columns": ["order_id", "customer_id", "total"],
                "data": [
                    [1001, 501, 1299.99],
                    [1002, 502, 849.99]
                ]
            }
        else:
            return {"success": False, "error": "Query failed"}
    
    tool.query_database.side_effect = mock_query_database
    
    return tool


@pytest.fixture
def mock_mindsdb_config():
    """Mock MindsDB config."""
    config = MagicMock()
    config.get_default_database.return_value = "htinfo_db"
    config.databases = [
        MagicMock(name="htinfo_db", description="主要业务数据库", default=True),
        MagicMock(name="ext_ref_db", description="外部参考数据", default=False)
    ]
    return config


@pytest.fixture
def patch_mindsdb_imports(mock_mindsdb_tool, mock_mindsdb_config):
    """Patch MindsDB imports."""
    with patch("src.graph.nodes_enhanced.MindsDBMCPTool", return_value=mock_mindsdb_tool):
        with patch("src.graph.nodes_enhanced.MindsDBMCPConfig.load_from_file", return_value=mock_mindsdb_config):
            yield


@pytest.mark.asyncio
async def test_database_query_node_success(
    mock_state,
    mock_config,
    patch_config_from_runnable_config,
    patch_mindsdb_imports,
    mock_mindsdb_tool
):
    """Test database_query_node with successful database queries."""
    result = await database_query_node(mock_state, mock_config)
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "database_query_results" in result
    assert isinstance(result["database_query_results"], str)
    
    # Verify that MindsDB methods were called
    mock_mindsdb_tool.get_available_databases.assert_called_once()
    mock_mindsdb_tool.get_table_info.assert_called()
    mock_mindsdb_tool.query_database.assert_called()
    
    # Check that results contain expected database information
    results = result["database_query_results"]
    assert "htinfo_db" in results
    assert "ext_ref_db" in results
    assert "walmart_online_item" in results
    assert "walmart_orders" in results


@pytest.mark.asyncio
async def test_database_query_node_no_databases(
    mock_state,
    mock_config,
    patch_config_from_runnable_config,
    patch_mindsdb_imports,
    mock_mindsdb_tool
):
    """Test database_query_node when no databases are available."""
    # Mock no databases available
    mock_mindsdb_tool.get_available_databases.return_value = []
    
    result = await database_query_node(mock_state, mock_config)
    
    assert isinstance(result, dict)
    assert "database_query_results" in result
    
    # Should contain message about no databases
    results = result["database_query_results"]
    assert "未找到可用的数据库连接" in results


@pytest.mark.asyncio
async def test_database_query_node_exception_handling(
    mock_state,
    mock_config,
    patch_config_from_runnable_config,
    patch_mindsdb_imports,
    mock_mindsdb_tool
):
    """Test database_query_node exception handling."""
    # Mock exception in get_available_databases
    mock_mindsdb_tool.get_available_databases.side_effect = Exception("Connection failed")
    
    result = await database_query_node(mock_state, mock_config)
    
    assert isinstance(result, dict)
    assert "database_query_results" in result
    
    results = result["database_query_results"]
    assert "数据库查询失败" in results
    assert "Connection failed" in results


def test_mindsdb_tool_initialization():
    """Test MindsDB tool can be initialized."""
    with patch("src.tools.mindsdb_mcp.requests"):
        from src.tools.mindsdb_mcp import MindsDBMCPTool
        
        tool = MindsDBMCPTool()
        assert tool.base_url == "http://localhost:47334"
        assert tool.api_url == "http://localhost:47334/api/sql/query"
        
        # Test with custom host and port
        tool_custom = MindsDBMCPTool("10.0.0.1", 8080)
        assert tool_custom.base_url == "http://10.0.0.1:8080"


def test_mindsdb_config_loading():
    """Test MindsDB config loading."""
    from src.config.mindsdb_mcp import MindsDBMCPConfig
    
    # Test default config
    config = MindsDBMCPConfig._get_default_config()
    assert config is not None
    assert len(config.databases) > 0
    assert len(config.tools) > 0
    assert config.get_default_database() is not None
    
    # Test agent tools
    researcher_tools = config.get_agent_tools("researcher")
    assert isinstance(researcher_tools, list)
    
    background_tools = config.get_agent_tools("background_investigator")
    assert isinstance(background_tools, list)