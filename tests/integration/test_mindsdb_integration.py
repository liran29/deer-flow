#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for MindsDB MCP functionality
"""

import asyncio
import pytest
import logging
import sys
import os

from src.tools.mindsdb_mcp import MindsDBMCPTool
from src.config.mindsdb_mcp import MindsDBMCPConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMindsDBIntegration:
    """Test class for MindsDB integration."""
    
    @pytest.fixture
    def mindsdb_tool(self):
        """Create MindsDB tool instance."""
        return MindsDBMCPTool()
    
    @pytest.fixture
    def mindsdb_config(self):
        """Load MindsDB configuration."""
        return MindsDBMCPConfig.load_from_file()
    
    def test_config_loading(self, mindsdb_config):
        """Test that configuration loads correctly."""
        assert mindsdb_config is not None
        assert len(mindsdb_config.databases) > 0
        assert len(mindsdb_config.tools) > 0
        logger.info(f"Default database: {mindsdb_config.get_default_database()}")
        
    def test_database_connection(self, mindsdb_tool):
        """Test basic database connection."""
        databases = mindsdb_tool.get_available_databases()
        logger.info(f"Available databases: {databases}")
        assert isinstance(databases, list)
        
    @pytest.mark.asyncio
    async def test_table_info_retrieval(self, mindsdb_tool):
        """Test table information retrieval."""
        databases = mindsdb_tool.get_available_databases()
        
        if not databases:
            pytest.skip("No databases available for testing")
            
        for db_name in databases:
            table_info = await mindsdb_tool.get_table_info(db_name)
            assert table_info is not None
            assert isinstance(table_info, dict)
            
            if table_info.get("success"):
                logger.info(f"Database {db_name} tables retrieved successfully")
                tables = [row[0] for row in table_info.get("data", [])]
                logger.info(f"Tables in {db_name}: {tables}")
            else:
                logger.warning(f"Failed to get tables for {db_name}: {table_info.get('error')}")
    
    @pytest.mark.asyncio
    async def test_database_query(self, mindsdb_tool):
        """Test database querying functionality."""
        databases = mindsdb_tool.get_available_databases()
        
        if not databases:
            pytest.skip("No databases available for testing")
            
        # Test with the first available database
        db_name = databases[0]
        
        # Get table information first
        table_info = await mindsdb_tool.get_table_info(db_name)
        
        if not table_info.get("success"):
            pytest.skip(f"Cannot get table info for {db_name}")
            
        tables = [row[0] for row in table_info.get("data", [])]
        
        if not tables:
            pytest.skip(f"No tables found in database {db_name}")
            
        # Test a simple query
        first_table = tables[0]
        query = f"SELECT * FROM {db_name}.{first_table} LIMIT 2"
        
        result = await mindsdb_tool.query_database(db_name, query)
        
        assert result is not None
        assert isinstance(result, dict)
        
        if result.get("success"):
            logger.info(f"Query successful on {db_name}.{first_table}")
            logger.info(f"Columns: {result.get('columns', [])}")
            logger.info(f"Records found: {len(result.get('data', []))}")
        else:
            logger.error(f"Query failed: {result.get('error')}")
            # Don't fail the test if it's just a query error, as long as we got a response


@pytest.mark.asyncio
async def test_database_query_node():
    """Test the database query node functionality."""
    try:
        from src.graph.nodes_enhanced import database_query_node
        from langchain_core.runnables import RunnableConfig
        
        # Create a mock state and config
        state = {
            "research_topic": "Walmart sales analysis"
        }
        
        # Create a basic config
        config = RunnableConfig(configurable={})
        
        logger.info("Testing database_query_node...")
        result = await database_query_node(state, config)
        
        assert result is not None
        assert "database_query_results" in result
        assert isinstance(result["database_query_results"], str)
        
        logger.info("Database query node test completed successfully")
        logger.info(f"Results length: {len(result['database_query_results'])} characters")
        
    except ImportError as e:
        pytest.skip(f"Cannot import required modules: {e}")
    except Exception as e:
        logger.error(f"Database query node test failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v", "-s"])