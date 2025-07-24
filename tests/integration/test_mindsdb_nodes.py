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
        from src.graph.nodes_enhanced import database_investigation_node


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
    
    # Mock get_table_metadata method (async) - fallback to basic structure info
    tool.get_table_metadata = AsyncMock()
    async def mock_get_table_metadata_basic(database, table):
        return {
            "success": False,  # Simulate fallback to basic method
            "error": "Enhanced metadata not available in basic test"
        }
    tool.get_table_metadata.side_effect = mock_get_table_metadata_basic
    
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
async def test_database_investigation_node_success(
    mock_state,
    mock_config,
    patch_config_from_runnable_config,
    patch_mindsdb_imports,
    mock_mindsdb_tool
):
    """Test database_investigation_node with successful database queries."""
    with patch("src.utils.enhanced_features.is_mindsdb_database_integration_enabled", return_value=True):
        result = await database_investigation_node(mock_state, mock_config)
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert "database_investigation_results" in result
    assert isinstance(result["database_investigation_results"], str)
    
    # Verify that MindsDB methods were called
    mock_mindsdb_tool.get_available_databases.assert_called_once()
    mock_mindsdb_tool.get_table_info.assert_called()
    # Note: query_database may not be called directly in enhanced metadata mode
    
    # Check that results contain expected database information
    results = result["database_investigation_results"]
    assert "htinfo_db" in results
    assert "ext_ref_db" in results
    assert "walmart_online_item" in results
    assert "walmart_orders" in results


@pytest.mark.asyncio
async def test_database_investigation_node_no_databases(
    mock_state,
    mock_config,
    patch_config_from_runnable_config,
    patch_mindsdb_imports,
    mock_mindsdb_tool
):
    """Test database_query_node when no databases are available."""
    # Mock no databases available
    mock_mindsdb_tool.get_available_databases.return_value = []
    
    with patch("src.utils.enhanced_features.is_mindsdb_database_integration_enabled", return_value=True):
        result = await database_investigation_node(mock_state, mock_config)
    
    assert isinstance(result, dict)
    assert "database_investigation_results" in result
    
    # Should return empty string when no databases available
    results = result["database_investigation_results"]
    assert results == ""


@pytest.mark.asyncio
async def test_database_investigation_node_exception_handling(
    mock_state,
    mock_config,
    patch_config_from_runnable_config,
    patch_mindsdb_imports,
    mock_mindsdb_tool
):
    """Test database_query_node exception handling."""
    # Mock exception in get_available_databases
    mock_mindsdb_tool.get_available_databases.side_effect = Exception("Connection failed")
    
    with patch("src.utils.enhanced_features.is_mindsdb_database_integration_enabled", return_value=True):
        result = await database_investigation_node(mock_state, mock_config)
    
    assert isinstance(result, dict)
    assert "database_investigation_results" in result
    
    results = result["database_investigation_results"]
    assert results == ""  # Should return empty string on error


@pytest.mark.asyncio 
async def test_database_investigation_node_disabled(mock_state, mock_config):
    """Test database_investigation_node when MindsDB integration is disabled."""
    with patch("src.utils.enhanced_features.is_mindsdb_database_integration_enabled", return_value=False):
        result = await database_investigation_node(mock_state, mock_config)
    
    assert isinstance(result, dict)
    assert "database_investigation_results" in result
    assert result["database_investigation_results"] == ""


@pytest.mark.asyncio 
async def test_database_investigation_node_enhanced_metadata(
    mock_state, mock_config, patch_config_from_runnable_config, patch_mindsdb_imports
):
    """Test database_investigation_node with enhanced metadata functionality."""
    
    # Mock enhanced MindsDB tool with metadata support
    mock_tool = MagicMock()
    mock_tool.get_available_databases.return_value = ["htinfo_db", "ext_ref_db"]
    
    # Mock basic table info
    mock_tool.get_table_info = AsyncMock()
    async def mock_get_table_info(database, table_name=None):
        if table_name:
            return {"success": True, "data": [["id", "int"], ["name", "varchar"]]}
        else:
            if database == "htinfo_db":
                return {"success": True, "data": [["walmart_online_item"], ["walmart_orders"]]}
            elif database == "ext_ref_db":
                return {"success": True, "data": [["reference_data"]]}
            else:
                return {"success": False, "error": "Database not found"}
    mock_tool.get_table_info.side_effect = mock_get_table_info
    
    # Mock enhanced metadata method
    async def mock_get_table_metadata(database, table):
        if table == "walmart_online_item":
            return {
                "success": True,
                "table_name": table,
                "database": database,
                "structure": [["id", "int", "primary key"], ["product_name", "varchar(255)", "not null"], ["price", "decimal(10,2)", "nullable"]],
                "statistics": {
                    "total_records": 1000,
                    "date_range": {
                        "column": "created_at",
                        "min": "2023-01-01",
                        "max": "2024-12-31"
                    }
                },
                "sample_data": [[1, "iPhone 15", 999.99], [2, "Samsung TV", 599.99]],
                "columns": ["id", "product_name", "price"],
                "enum_values": {
                    "category": ["Electronics", "Clothing", "Home"]
                }
            }
        elif table == "walmart_orders":
            return {
                "success": True,
                "table_name": table,
                "database": database,
                "structure": [["order_id", "int", "primary key"], ["customer_id", "int", "not null"], ["total", "decimal(10,2)", "not null"]],
                "statistics": {
                    "total_records": 500,
                    "date_range": {
                        "column": "order_date",
                        "min": "2023-06-01",
                        "max": "2024-11-30"
                    }
                },
                "sample_data": [[1001, 501, 1299.99], [1002, 502, 849.99]],
                "columns": ["order_id", "customer_id", "total"],
                "enum_values": {
                    "status": ["pending", "shipped", "delivered", "cancelled"]
                }
            }
        elif table == "reference_data":
            return {
                "success": True,
                "table_name": table,
                "database": database,
                "structure": [["ref_id", "int", "primary key"], ["data_type", "varchar(100)", "not null"], ["value", "text", "nullable"]],
                "statistics": {
                    "total_records": 200,
                    "date_range": {
                        "column": "updated_at",
                        "min": "2023-01-15",
                        "max": "2024-12-01"
                    }
                },
                "sample_data": [[1, "exchange_rate", "1.0"], [2, "tax_rate", "0.08"]],
                "columns": ["ref_id", "data_type", "value"],
                "enum_values": {
                    "data_type": ["exchange_rate", "tax_rate", "discount_rate", "shipping_rate"]
                }
            }
        else:
            return {
                "success": False,
                "error": f"Table {table} not found"
            }
    mock_tool.get_table_metadata = AsyncMock(side_effect=mock_get_table_metadata)
    
    with patch("src.graph.nodes_enhanced.MindsDBMCPTool", return_value=mock_tool):
        with patch("src.graph.nodes_enhanced.MindsDBMCPConfig.load_from_file"):
            with patch("src.utils.enhanced_features.is_mindsdb_database_integration_enabled", return_value=True):
                result = await database_investigation_node(mock_state, mock_config)
    
    assert isinstance(result, dict)
    assert "database_investigation_results" in result
    results = result["database_investigation_results"]
    
    # 验证增强的元数据信息
    assert "总记录数: 1000" in results
    assert "时间范围: 2023-01-01 至 2024-12-31" in results
    assert "category: Electronics, Clothing, Home" in results
    assert "样本数据" in results
    assert "iPhone 15" in results
    assert "Samsung TV" in results
    
    # 验证walmart_orders表的信息
    assert "总记录数: 500" in results
    assert "时间范围: 2023-06-01 至 2024-11-30" in results
    assert "status: pending, shipped, delivered, cancelled" in results
    
    # 验证reference_data表的信息
    assert "总记录数: 200" in results
    assert "data_type: exchange_rate, tax_rate, discount_rate, shipping_rate" in results


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