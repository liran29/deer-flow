# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import json
from typing import Any, Dict, List, Optional
import requests

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
            # Format query to use specific database
            full_query = f"SELECT * FROM ({query}) AS subquery"
            if not query.upper().startswith('SELECT'):
                full_query = query
                
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
                query = f"DESCRIBE {database}.{table_name};"
            else:
                query = f"SHOW TABLES FROM {database};"
                
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