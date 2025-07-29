# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import json
from typing import Any, Dict, List, Optional, Annotated
import requests
from langchain_core.tools import tool
from .decorators import log_io

logger = logging.getLogger(__name__)


class MindsDBMCPTool:
    """MindsDB MCP Tool for querying databases and AI models via MindsDB API."""
    
    def __init__(self, mindsdb_host: str = "localhost", mindsdb_port: int = 47334):
        """
        Initialize MindsDB MCP Tool.
        
        Args:
            mindsdb_host: MindsDB HTTP API host
            mindsdb_port: MindsDB HTTP API port
        """
        self.base_url = f"http://{mindsdb_host}:{mindsdb_port}"
        self.api_url = f"{self.base_url}/api/sql/query"
        
    async def query_database(self, database: str, query: str) -> Dict[str, Any]:
        """
        Execute SQL queries on connected databases.
        
        Args:
            database: Database name (e.g., 'htinfo_db', 'ext_ref_db')
            query: SQL query to execute
            
        Returns:
            Query results as dictionary
        """
        try:
            # Ensure table references include database name
            full_query = query
            
            # If query contains FROM clause without database prefix, add it
            import re
            if database and 'FROM' in query.upper():
                # Pattern to match FROM table_name where table_name doesn't have a dot
                pattern = r'FROM\s+([^\s.]+)(?:\s|$)'
                def replace_table(match):
                    table = match.group(1)
                    # Only add database prefix if table doesn't already have one
                    if '.' not in table and not table.upper() in ['(', 'SELECT']:
                        return f'FROM {database}.{table} '
                    return match.group(0)
                
                full_query = re.sub(pattern, replace_table, query, flags=re.IGNORECASE)
                
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={"query": full_query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result.get("data", []),
                    "columns": result.get("column_names", []),
                    "query": full_query
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "query": full_query
                }
                
        except Exception as e:
            logger.error(f"Error executing database query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def get_table_info(self, database: str, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get table structure information.
        
        Args:
            database: Database name
            table_name: Specific table name, if None returns all tables
            
        Returns:
            Table information as dictionary
        """
        try:
            if table_name:
                # Use SELECT to get table structure from information_schema
                query = f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = '{database}' AND table_name = '{table_name}';"
            else:
                query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{database}';"
                
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "database": database,
                    "table_name": table_name,
                    "data": result.get("data", []),
                    "columns": result.get("column_names", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "database": database,
                    "table_name": table_name
                }
                
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "database": database,
                "table_name": table_name
            }
    
    async def natural_language_query(self, question: str, database: str) -> Dict[str, Any]:
        """
        Convert natural language to SQL and execute (placeholder for AI model).
        
        Args:
            question: Natural language question
            database: Database to query
            
        Returns:
            Query results as dictionary
        """
        try:
            # For now, this is a placeholder since DeepSeek models have issues
            # In the future, this would use a working AI model to convert NL to SQL
            return {
                "success": False,
                "error": "Natural language query feature is not yet available due to AI model configuration issues",
                "question": question,
                "database": database,
                "suggested_action": "Please use direct SQL queries via query_database method"
            }
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "question": question,
                "database": database
            }
    
    async def analyze_data(self, data: List[Dict[str, Any]], analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Analyze data and generate insights (placeholder for AI model).
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results as dictionary
        """
        try:
            # For now, provide basic statistical analysis without AI
            if not data:
                return {
                    "success": False,
                    "error": "No data provided for analysis",
                    "analysis_type": analysis_type
                }
            
            # Basic data analysis
            num_records = len(data)
            columns = list(data[0].keys()) if data else []
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "summary": {
                    "total_records": num_records,
                    "columns": columns,
                    "column_count": len(columns)
                },
                "note": "Advanced AI-powered analysis will be available once AI models are properly configured"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    async def get_table_metadata(self, database: str, table: str) -> Dict[str, Any]:
        """
        获取表的详细元数据信息，包括统计信息、枚举值等
        
        Args:
            database: 数据库名
            table: 表名
            
        Returns:
            包含元数据的字典
        """
        try:
            metadata = {
                "success": True,
                "table_name": table,
                "database": database,
                "structure": None,
                "statistics": {},
                "sample_data": [],
                "enum_values": {}
            }
            
            # 1. 获取表结构
            structure_result = await self.get_table_info(database, table)
            if structure_result.get("success"):
                metadata["structure"] = structure_result.get("data", [])
            
            # 2. 获取基本统计信息
            try:
                count_query = f"SELECT COUNT(*) as total_records FROM {database}.{table}"
                count_result = await self.query_database(database, count_query)
                if count_result.get("success") and count_result.get("data"):
                    metadata["statistics"]["total_records"] = count_result["data"][0][0]
            except:
                pass
            
            # 3. 获取样本数据
            try:
                sample_query = f"SELECT * FROM {database}.{table} LIMIT 3"
                sample_result = await self.query_database(database, sample_query)
                if sample_result.get("success"):
                    metadata["sample_data"] = sample_result.get("data", [])
                    metadata["columns"] = sample_result.get("columns", [])
            except:
                pass
            
            # 4. 获取字符串字段的枚举值（前10个）
            if metadata.get("columns"):
                for i, column in enumerate(metadata["columns"]):
                    try:
                        # 尝试获取该字段的不同值
                        enum_query = f"SELECT DISTINCT {column} FROM {database}.{table} WHERE {column} IS NOT NULL LIMIT 10"
                        enum_result = await self.query_database(database, enum_query)
                        if enum_result.get("success") and enum_result.get("data"):
                            values = [row[0] for row in enum_result["data"] if row[0] is not None]
                            if values and len(values) <= 10:  # 只有少量不同值时才认为是枚举
                                metadata["enum_values"][column] = values
                    except:
                        continue
            
            # 5. 获取时间范围（如果有时间字段）
            time_columns = ["created_at", "updated_at", "date", "time", "timestamp"]
            if metadata.get("columns"):
                for column in metadata["columns"]:
                    if any(time_col in column.lower() for time_col in time_columns):
                        try:
                            range_query = f"SELECT MIN({column}) as min_date, MAX({column}) as max_date FROM {database}.{table} WHERE {column} IS NOT NULL"
                            range_result = await self.query_database(database, range_query)
                            if range_result.get("success") and range_result.get("data"):
                                min_date, max_date = range_result["data"][0]
                                if min_date and max_date:
                                    metadata["statistics"]["date_range"] = {
                                        "column": column,
                                        "min": str(min_date),
                                        "max": str(max_date)
                                    }
                                    break
                        except:
                            continue
            
            return metadata
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get table metadata: {str(e)}"
            }
    
    def get_available_databases(self) -> List[str]:
        """
        Get list of available databases.
        
        Returns:
            List of database names
        """
        try:
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={"query": "SELECT * FROM information_schema.databases WHERE type='data';"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                databases = [row[0] for row in result.get("data", []) if row[0] not in ['information_schema', 'log', 'mindsdb', 'files']]
                return databases
            else:
                logger.error(f"Failed to get databases: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting available databases: {str(e)}")
            return []


# Create a global instance for the tool
_mindsdb_instance = MindsDBMCPTool()


@tool
@log_io
def mindsdb_query_tool(
    query: Annotated[str, "SQL query to execute on the database"],
    database: Annotated[str, "Database name to query (e.g., 'htinfo_db')"] = "htinfo_db"
) -> str:
    """Execute SQL queries on MindsDB connected databases. Use this tool to query data from available databases."""
    try:
        # Convert async method to sync for LangChain compatibility
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_mindsdb_instance.query_database(database, query))
        
        if result.get("success"):
            data = result.get("data", [])
            row_count = len(data)
            # Only show first 3 rows as examples
            sample_data = data[:3] if row_count > 3 else data
            
            return json.dumps({
                "success": True,
                "query": query,
                "database": database,
                "data": sample_data,
                "columns": result.get("columns", []),
                "total_rows": row_count,
                "message": f"Query executed successfully. Retrieved {row_count} rows. Showing {len(sample_data)} sample rows."
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "success": False,
                "query": query,
                "database": database,
                "error": result.get("error", "Unknown error"),
                "message": "Query execution failed."
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"MindsDB query tool error: {str(e)}")
        return json.dumps({
            "success": False,
            "query": query,
            "database": database,
            "error": str(e),
            "message": "Tool execution failed."
        }, ensure_ascii=False, indent=2)


@tool  
@log_io
def mindsdb_table_info_tool(
    database: Annotated[str, "Database name"] = "htinfo_db",
    table_name: Annotated[str, "Table name (optional, shows all tables if not specified)"] = None
) -> str:
    """Get information about database tables including structure and metadata."""
    try:
        # Convert async method to sync for LangChain compatibility
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_mindsdb_instance.get_table_info(database, table_name))
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"MindsDB table info tool error: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to get table information."
        }, ensure_ascii=False, indent=2)