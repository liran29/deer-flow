# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class MCPServerConfig:
    """MindsDB MCP Server configuration."""
    host: str = "localhost"
    port: int = 47337
    protocol: str = "mcp"

@dataclass
class DatabaseConfig:
    """Database configuration."""
    name: str
    description: str
    default: bool = False

@dataclass
class ModelConfig:
    """AI Model configuration."""
    name: str
    description: str
    input_params: List[str] = field(default_factory=list)

@dataclass
class ToolConfig:
    """MCP Tool configuration."""
    name: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)

@dataclass
class AgentIntegrationConfig:
    """Agent integration configuration."""
    tools: List[str] = field(default_factory=list)
    prompt_addon: str = ""

@dataclass
class MindsDBMCPConfig:
    """Complete MindsDB MCP configuration."""
    server: MCPServerConfig = field(default_factory=MCPServerConfig)
    databases: List[DatabaseConfig] = field(default_factory=list)
    models: List[ModelConfig] = field(default_factory=list)
    tools: List[ToolConfig] = field(default_factory=list)
    agent_integration: Dict[str, AgentIntegrationConfig] = field(default_factory=dict)
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "MindsDBMCPConfig":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file, defaults to config/mindsdb_mcp.yaml
            
        Returns:
            MindsDBMCPConfig instance
        """
        if config_path is None:
            # Default to config/mindsdb_mcp.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "mindsdb_mcp.yaml"
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            # Return default configuration if file doesn't exist
            return cls._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data or 'mindsdb_mcp' not in config_data:
                return cls._get_default_config()
            
            mcp_config = config_data['mindsdb_mcp']
            
            # Parse server config
            server_data = mcp_config.get('server', {})
            server = MCPServerConfig(
                host=server_data.get('host', 'localhost'),
                port=server_data.get('port', 47337),
                protocol=server_data.get('protocol', 'mcp')
            )
            
            # Parse databases
            databases = []
            for db_data in mcp_config.get('databases', []):
                databases.append(DatabaseConfig(
                    name=db_data['name'],
                    description=db_data['description'],
                    default=db_data.get('default', False)
                ))
            
            # Parse models
            models = []
            for model_data in mcp_config.get('models', []):
                models.append(ModelConfig(
                    name=model_data['name'],
                    description=model_data['description'],
                    input_params=model_data.get('input_params', [])
                ))
            
            # Parse tools
            tools = []
            for tool_data in mcp_config.get('tools', []):
                tools.append(ToolConfig(
                    name=tool_data['name'],
                    description=tool_data['description'],
                    parameters=tool_data.get('parameters', {})
                ))
            
            # Parse agent integrations
            agent_integration = {}
            for agent_name, agent_data in mcp_config.get('agent_integration', {}).items():
                agent_integration[agent_name] = AgentIntegrationConfig(
                    tools=agent_data.get('tools', []),
                    prompt_addon=agent_data.get('prompt_addon', '')
                )
            
            return cls(
                server=server,
                databases=databases,
                models=models,
                tools=tools,
                agent_integration=agent_integration
            )
            
        except Exception as e:
            print(f"Error loading MindsDB MCP config: {e}")
            return cls._get_default_config()
    
    @classmethod
    def _get_default_config(cls) -> "MindsDBMCPConfig":
        """Get default configuration."""
        return cls(
            server=MCPServerConfig(),
            databases=[
                DatabaseConfig(name="htinfo_db", description="主要业务数据库", default=True),
                DatabaseConfig(name="ext_ref_db", description="外部参考数据")
            ],
            models=[
                ModelConfig(
                    name="nl2sql_model",
                    description="自然语言转SQL查询",
                    input_params=["database", "tables", "question"]
                ),
                ModelConfig(
                    name="data_insights",
                    description="数据分析和洞察生成",
                    input_params=["data"]
                )
            ],
            tools=[
                ToolConfig(
                    name="query_database",
                    description="Execute SQL queries on connected databases",
                    parameters={"database": "string", "query": "string"}
                ),
                ToolConfig(
                    name="analyze_data",
                    description="Analyze data and generate insights",
                    parameters={"data": "object", "analysis_type": "string"}
                ),
                ToolConfig(
                    name="get_table_info",
                    description="Get table structure information",
                    parameters={"database": "string", "table_name": "string"}
                ),
                ToolConfig(
                    name="natural_language_query",
                    description="Convert natural language to SQL and execute",
                    parameters={"question": "string", "database": "string"}
                )
            ],
            agent_integration={
                "background_investigator": AgentIntegrationConfig(
                    tools=["get_table_info", "query_database"],
                    prompt_addon="You have access to database: {{database_info}}\nUse get_table_info to understand data structure before planning."
                ),
                "researcher": AgentIntegrationConfig(
                    tools=["natural_language_query", "analyze_data", "query_database"],
                    prompt_addon="You can query local databases for accurate data.\nPrefer database queries over web search when data is available locally."
                )
            }
        )
    
    def get_default_database(self) -> Optional[str]:
        """Get the default database name."""
        for db in self.databases:
            if db.default:
                return db.name
        return self.databases[0].name if self.databases else None
    
    def get_agent_tools(self, agent_name: str) -> List[str]:
        """Get tools available for a specific agent."""
        if agent_name in self.agent_integration:
            return self.agent_integration[agent_name].tools
        return []
    
    def get_agent_prompt_addon(self, agent_name: str) -> str:
        """Get prompt addon for a specific agent."""
        if agent_name in self.agent_integration:
            return self.agent_integration[agent_name].prompt_addon
        return ""