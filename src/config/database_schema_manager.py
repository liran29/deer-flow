"""数据库Schema配置管理器

支持静态配置和动态获取两种模式，提供灵活的数据库元数据管理。
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseSchemaManager:
    """数据库Schema配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "config", 
            "database_schema.yaml"
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"数据库配置加载成功: {self.config_file}")
                return config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"配置文件加载失败: {str(e)}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "mode": "dynamic",
            "settings": {
                "max_tables_per_database": 3,
                "max_fields_per_table": 5,
                "max_sample_records": 2,
                "enable_statistics": True,
                "enable_enum_values": True,
                "enable_sample_data": True
            },
            "databases": {},
            "dynamic_config": {
                "fallback_to_dynamic": True,
                "database_filter": {
                    "include": ["htinfo_db", "ext_ref_db"],
                    "exclude": ["information_schema", "mysql", "performance_schema"]
                },
                "table_filter": {
                    "exclude_patterns": ["tmp_*", "temp_*", "_backup", "log_*"],
                    "include_patterns": ["*"]
                }
            }
        }
    
    def get_mode(self) -> str:
        """获取配置模式: static, dynamic, hybrid"""
        return self.config.get("mode", "dynamic")
    
    def get_settings(self) -> Dict[str, Any]:
        """获取全局设置"""
        return self.config.get("settings", {})
    
    def get_database_config(self, database_name: str) -> Optional[Dict[str, Any]]:
        """获取数据库配置"""
        databases = self.config.get("databases", {})
        return databases.get(database_name)
    
    def get_table_config(self, database_name: str, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表配置"""
        db_config = self.get_database_config(database_name)
        if db_config and "tables" in db_config:
            return db_config["tables"].get(table_name)
        return None
    
    def is_database_enabled(self, database_name: str) -> bool:
        """检查数据库是否启用"""
        db_config = self.get_database_config(database_name)
        if db_config:
            return db_config.get("enabled", True)
        
        # 如果没有静态配置，检查动态配置过滤规则
        dynamic_config = self.config.get("dynamic_config", {})
        db_filter = dynamic_config.get("database_filter", {})
        
        # 检查包含列表
        include_list = db_filter.get("include", [])
        if include_list and database_name not in include_list:
            return False
        
        # 检查排除列表
        exclude_list = db_filter.get("exclude", [])
        if database_name in exclude_list:
            return False
        
        return True
    
    def should_include_table(self, table_name: str) -> bool:
        """检查表是否应该包含（基于过滤规则）"""
        dynamic_config = self.config.get("dynamic_config", {})
        table_filter = dynamic_config.get("table_filter", {})
        
        # 检查排除模式
        exclude_patterns = table_filter.get("exclude_patterns", [])
        for pattern in exclude_patterns:
            if self._match_pattern(table_name, pattern):
                return False
        
        # 检查包含模式
        include_patterns = table_filter.get("include_patterns", ["*"])
        for pattern in include_patterns:
            if self._match_pattern(table_name, pattern):
                return True
        
        return False
    
    def _match_pattern(self, text: str, pattern: str) -> bool:
        """简单的模式匹配（支持*通配符）"""
        if pattern == "*":
            return True
        if "*" not in pattern:
            return text == pattern
        
        # 简化的通配符匹配
        if pattern.startswith("*"):
            return text.endswith(pattern[1:])
        if pattern.endswith("*"):
            return text.startswith(pattern[:-1])
        
        return text == pattern
    
    def format_static_database_info(self, database_name: str) -> str:
        """格式化静态数据库信息"""
        db_config = self.get_database_config(database_name)
        if not db_config:
            return ""
        
        settings = self.get_settings()
        max_tables = settings.get("max_tables_per_database", 3)
        
        result = f"\n\n## 数据库 {database_name}\n"
        result += f"{db_config.get('description', '')}\n"
        
        # 获取表列表
        tables = db_config.get("tables", {})
        # 按优先级排序
        sorted_tables = sorted(
            tables.items(), 
            key=lambda x: x[1].get("priority", 999)
        )[:max_tables]
        
        table_names = [table_name for table_name, _ in sorted_tables]
        result += f"可用表: {', '.join(table_names)}\n"
        
        # 详细表信息
        for table_name, table_config in sorted_tables:
            result += self.format_static_table_info(table_name, table_config)
        
        return result
    
    def format_static_table_info(self, table_name: str, table_config: Dict[str, Any]) -> str:
        """格式化静态表信息"""
        settings = self.get_settings()
        max_fields = settings.get("max_fields_per_table", 5)
        max_samples = settings.get("max_sample_records", 2)
        
        result = f"\n### 表 {table_name} 详细信息:\n"
        result += f"{table_config.get('description', '')}\n\n"
        
        # 字段结构
        fields = table_config.get("fields", [])[:max_fields]
        if fields and settings.get("enable_statistics", True):
            result += "**字段结构:**\n"
            for field in fields:
                field_desc = f"{field['name']} ({field['type']})"
                if field.get("description"):
                    field_desc += f" - {field['description']}"
                if field.get("is_primary_key"):
                    field_desc += " [主键]"
                result += f"  - {field_desc}\n"
        
        # 统计信息
        statistics = table_config.get("statistics", {})
        if statistics and settings.get("enable_statistics", True):
            result += "\n**统计信息:**\n"
            if "total_records" in statistics:
                result += f"  - 总记录数: {statistics['total_records']}\n"
            if "date_range" in statistics:
                dr = statistics["date_range"]
                result += f"  - 时间范围: {dr['min']} 至 {dr['max']} ({dr['column']})\n"
        
        # 枚举值
        if settings.get("enable_enum_values", True):
            enum_fields = [f for f in fields if "enum_values" in f]
            if enum_fields:
                result += "\n**字段取值范围:**\n"
                for field in enum_fields:
                    values = field["enum_values"]
                    result += f"  - {field['name']}: {', '.join(map(str, values))}\n"
        
        # 样本数据
        sample_data = table_config.get("sample_data", [])
        if sample_data and settings.get("enable_sample_data", True):
            result += "\n**样本数据:**\n"
            field_names = [f["name"] for f in fields]
            result += f"列名: {', '.join(field_names)}\n"
            for i, row in enumerate(sample_data[:max_samples]):
                result += f"  记录{i+1}: {row}\n"
        
        return result
    
    def get_enabled_databases(self) -> List[str]:
        """获取启用的数据库列表"""
        if self.get_mode() == "static":
            # 静态模式：从配置文件获取
            databases = self.config.get("databases", {})
            return [
                db_name for db_name, db_config in databases.items() 
                if db_config.get("enabled", True)
            ]
        else:
            # 动态或混合模式：从过滤规则获取
            dynamic_config = self.config.get("dynamic_config", {})
            db_filter = dynamic_config.get("database_filter", {})
            return db_filter.get("include", ["htinfo_db", "ext_ref_db"])
    
    def should_fallback_to_dynamic(self) -> bool:
        """是否应该回退到动态获取"""
        if self.get_mode() == "static":
            return False
        return self.config.get("dynamic_config", {}).get("fallback_to_dynamic", True)


    async def get_database_info(self, mode: Optional[str] = None) -> str:
        """根据配置模式获取数据库信息
        
        Args:
            mode: 指定模式，如果不指定则使用配置文件中的模式
            
        Returns:
            格式化的数据库信息字符串
        """
        mode = mode or self.get_mode()
        
        if mode == "static":
            # 静态模式：从配置文件获取所有信息
            return await self.get_static_database_info()
        elif mode == "dynamic":
            # 动态模式：从实际数据库获取信息
            return await self.get_dynamic_database_info()
        elif mode == "hybrid":
            # 混合模式：优先使用静态配置，失败时回退到动态获取
            return await self.get_hybrid_database_info()
        else:
            logger.error(f"Unknown mode: {mode}")
            return ""
    
    async def get_static_database_info(self) -> str:
        """从静态配置获取数据库信息"""
        logger.info("使用静态配置获取数据库信息")
        
        results = ""
        enabled_databases = self.get_enabled_databases()
        
        for db_name in enabled_databases:
            if self.is_database_enabled(db_name):
                db_info = self.format_static_database_info(db_name)
                results += db_info
        
        return results
    
    async def get_dynamic_database_info(self) -> str:
        """从实际数据库动态获取信息"""
        logger.info("使用动态模式获取数据库信息")
        
        try:
            # 延迟导入，避免循环依赖
            from src.tools.mindsdb_mcp import MindsDBMCPTool
            
            # 初始化MindsDB工具
            mindsdb_tool = MindsDBMCPTool()
            available_databases = mindsdb_tool.get_available_databases()
            logger.info(f"可用数据库: {available_databases}")
            
            results = ""
            settings = self.get_settings()
            max_tables = settings.get("max_tables_per_database", 3)
            
            for db_name in available_databases:
                if not self.is_database_enabled(db_name):
                    continue
                    
                table_info = await mindsdb_tool.get_table_info(db_name)
                
                if table_info.get("success"):
                    tables = [row[0] for row in table_info.get("data", [])]
                    # 过滤表名
                    filtered_tables = [
                        table for table in tables 
                        if self.should_include_table(table)
                    ][:max_tables]
                    
                    logger.info(f"数据库 {db_name} 中的表: {filtered_tables}")
                    results += f"\n\n## 数据库 {db_name}\n可用表: {', '.join(filtered_tables)}\n"
                    
                    # 为每个表获取详细元数据
                    for table in filtered_tables:
                        try:
                            logger.info(f"获取表 {table} 的详细元数据...")
                            metadata = await mindsdb_tool.get_table_metadata(db_name, table)
                            
                            if metadata.get("success"):
                                results += self._format_dynamic_table_info(table, metadata, settings)
                            else:
                                # 降级到基本方法
                                logger.warning(f"元数据获取失败，使用基本方法: {metadata.get('error')}")
                                structure_info = await mindsdb_tool.get_table_info(db_name, table)
                                if structure_info.get("success"):
                                    results += f"\n### 表 {table} 基本信息:\n"
                                    for row in structure_info.get("data", [])[:settings.get("max_fields_per_table", 5)]:
                                        results += f"  - {row}\n"
                                        
                        except Exception as e:
                            logger.warning(f"查询表 {table} 元数据失败: {str(e)}")
                            results += f"\n### 表 {table}: 查询失败 - {str(e)}\n"
                else:
                    results += f"\n\n## 数据库 {db_name}: 无法获取表信息\n"
            
            return results
            
        except Exception as e:
            logger.error(f"动态数据库查询过程出错: {str(e)}")
            return ""
    
    async def get_hybrid_database_info(self) -> str:
        """混合模式：优先静态配置，失败时动态获取"""
        logger.info("使用混合模式获取数据库信息")
        
        # 先尝试静态配置
        static_results = await self.get_static_database_info()
        
        if static_results and not self.should_fallback_to_dynamic():
            return static_results
        
        # 如果静态配置为空或配置允许回退，使用动态获取
        logger.info("静态配置不足，回退到动态获取")
        dynamic_results = await self.get_dynamic_database_info()
        
        # 合并结果（如果两者都有）
        if static_results and dynamic_results:
            return static_results + "\n\n--- 以下为动态获取的补充信息 ---\n" + dynamic_results
        
        return static_results or dynamic_results
    
    def _format_dynamic_table_info(self, table_name: str, metadata: dict, settings: dict) -> str:
        """格式化动态获取的表信息"""
        results = f"\n### 表 {table_name} 详细信息:\n"
        
        # 表结构
        if metadata.get("structure") and settings.get("enable_statistics", True):
            results += "**字段结构:**\n"
            for row in metadata["structure"][:settings.get("max_fields_per_table", 5)]:
                results += f"  - {row}\n"
        
        # 统计信息
        if metadata.get("statistics") and settings.get("enable_statistics", True):
            stats = metadata["statistics"]
            results += "\n**统计信息:**\n"
            if "total_records" in stats:
                results += f"  - 总记录数: {stats['total_records']}\n"
            if "date_range" in stats:
                dr = stats["date_range"]
                results += f"  - 时间范围: {dr['min']} 至 {dr['max']} ({dr['column']})\n"
        
        # 枚举值
        if metadata.get("enum_values") and settings.get("enable_enum_values", True):
            results += "\n**字段取值范围:**\n"
            for column, values in metadata["enum_values"].items():
                results += f"  - {column}: {', '.join(map(str, values))}\n"
        
        # 样本数据
        if (metadata.get("sample_data") and metadata.get("columns") and 
            settings.get("enable_sample_data", True)):
            results += "\n**样本数据:**\n"
            results += f"列名: {', '.join(metadata['columns'])}\n"
            max_samples = settings.get("max_sample_records", 2)
            for i, row in enumerate(metadata["sample_data"][:max_samples]):
                results += f"  记录{i+1}: {row}\n"
        
        return results


# 全局实例
_schema_manager = None

def get_database_schema_manager() -> DatabaseSchemaManager:
    """获取数据库Schema管理器单例"""
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = DatabaseSchemaManager()
    return _schema_manager