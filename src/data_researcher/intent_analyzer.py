"""
数据意图识别器 (Data Intent Analyzer)

深度理解用户查询，识别数据分析意图，类似于deep-research中的背景调查，
但专注于数据需求分析。

设计原则：
1. LLM提示词存储在单独的markdown文件中
2. 所有dict的key字段使用英文
3. 数据库信息从markdown文件或MindsDB MCP获取
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..llms.llm import get_llm_by_type
from ..tools.mindsdb_mcp import MindsDBMCPTool

logger = logging.getLogger(__name__)

# 获取当前文件所在目录
CURRENT_DIR = Path(__file__).parent


class AnalysisType(Enum):
    """数据分析类型枚举"""
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic" 
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"


class BusinessDomain(Enum):
    """业务领域枚举"""
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    GENERAL = "general"


@dataclass
class DataAnalysisIntent:
    """数据分析意图完整定义"""
    # 核心意图
    business_objective: str
    business_domain: str
    analysis_type: str
    
    # 数据需求
    primary_entities: List[Dict[str, Any]]
    secondary_entities: List[Dict[str, Any]]
    analysis_dimensions: List[Dict[str, Any]]
    target_metrics: List[Dict[str, Any]]
    
    # 分析要求
    time_range: Optional[str]
    filter_conditions: List[Dict[str, Any]]
    data_relationships: List[Dict[str, Any]]
    
    # 输出要求
    expected_insights: List[str]
    visualization_needs: List[str]
    report_format: str
    
    # 技术要求
    data_quality_requirements: List[str]
    performance_requirements: Dict[str, Any]
    
    # 元数据
    confidence_score: float
    complexity_level: str
    estimated_execution_time: str


class PromptTemplateLoader:
    """提示词模板加载器"""
    
    def __init__(self, prompts_dir: str):
        self.prompts_dir = Path(prompts_dir)
    
    def load_template(self, template_name: str) -> str:
        """加载指定的提示词模板"""
        template_path = self.prompts_dir / f"{template_name}.md"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取模板内容（在```标记之间的内容）
        lines = content.split('\n')
        template_content = []
        in_template = False
        
        for line in lines:
            if line.strip() == '```' and in_template:
                break
            elif in_template:
                template_content.append(line)
            elif line.strip() == '```':
                in_template = True
        
        return '\n'.join(template_content)


class SchemaLoader:
    """数据库结构加载器"""
    
    def __init__(self, schemas_dir: str):
        self.schemas_dir = Path(schemas_dir)
        self._entity_mappings = None
        self._database_schema = None
    
    def load_entity_mappings(self) -> Dict[str, Any]:
        """加载实体映射配置"""
        if self._entity_mappings is None:
            mapping_path = self.schemas_dir / "entity_mappings.md"
            self._entity_mappings = self._extract_json_from_markdown(mapping_path)
        return self._entity_mappings
    
    def load_database_schema(self) -> Dict[str, Any]:
        """加载数据库结构信息"""
        if self._database_schema is None:
            schema_path = self.schemas_dir / "database_schema.md"
            self._database_schema = self._parse_database_schema(schema_path)
        return self._database_schema
    
    def _extract_json_from_markdown(self, file_path: Path) -> Dict[str, Any]:
        """从markdown文件中提取JSON配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取所有JSON块
        json_blocks = []
        lines = content.split('\n')
        current_json = []
        in_json = False
        
        for line in lines:
            if line.strip() == '```json':
                in_json = True
                current_json = []
            elif line.strip() == '```' and in_json:
                try:
                    json_obj = json.loads('\n'.join(current_json))
                    json_blocks.append(json_obj)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON block in {file_path}")
                in_json = False
            elif in_json:
                current_json.append(line)
        
        return {"entities": json_blocks}
    
    def _parse_database_schema(self, file_path: Path) -> Dict[str, Any]:
        """解析数据库结构markdown文件"""
        # 这里可以实现更复杂的解析逻辑
        # 暂时返回基础结构
        return {
            "htinfo_db": {
                "walmart_orders": {
                    "description": "沃尔玛订单数据表",
                    "key_fields": ["order_id", "order_date", "total_amount", "customer_id"]
                },
                "walmart_online_item": {
                    "description": "沃尔玛在线商品数据表", 
                    "key_fields": ["item_id", "category", "RetailPrice", "brand"]
                }
            },
            "ext_ref_db": {
                "reference_data": {
                    "description": "外部参考数据表",
                    "key_fields": ["ref_id", "ref_type", "ref_key", "ref_value"]
                }
            }
        }


class DataIntentAnalyzer:
    """
    数据意图识别器
    
    遵循新的设计规范：
    1. 使用markdown文件存储提示词模板
    2. 所有dict的key使用英文
    3. 从配置文件加载数据库信息
    """
    
    def __init__(self):
        self.llm = None
        self.mindsdb_tool = None
        
        # 初始化加载器
        self.prompt_loader = PromptTemplateLoader(CURRENT_DIR / "prompts")
        self.schema_loader = SchemaLoader(CURRENT_DIR / "schemas")
        
        # 缓存加载的配置
        self._entity_mappings = None
        self._database_schema = None
    
    async def _ensure_dependencies(self):
        """确保依赖组件已初始化"""
        if self.llm is None:
            self.llm = get_llm_by_type("basic")
        if self.mindsdb_tool is None:
            self.mindsdb_tool = MindsDBMCPTool()
    
    def _get_entity_mappings(self) -> Dict[str, Any]:
        """获取实体映射配置"""
        if self._entity_mappings is None:
            self._entity_mappings = self.schema_loader.load_entity_mappings()
        return self._entity_mappings
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """获取数据库结构信息"""
        if self._database_schema is None:
            self._database_schema = self.schema_loader.load_database_schema()
        return self._database_schema
    
    async def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> DataAnalysisIntent:
        """
        分析用户查询，提取数据分析意图
        
        Args:
            query: 用户的原始查询
            context: 可选的上下文信息
            
        Returns:
            DataAnalysisIntent: 解析出的数据分析意图
        """
        await self._ensure_dependencies()
        
        try:
            logger.info(f"开始分析用户查询意图: {query}")
            
            # 1. 基础意图提取
            basic_analysis = await self._extract_basic_intent(query)
            
            # 2. 业务上下文分析
            business_context = await self._analyze_business_context(query, basic_analysis)
            
            # 3. 数据需求分析
            data_requirements = await self._analyze_data_requirements(query, business_context)
            
            # 4. 技术需求分析
            technical_requirements = await self._analyze_technical_requirements(query, data_requirements)
            
            # 5. 综合形成完整意图
            complete_intent = self._synthesize_intent(
                query, basic_analysis, business_context, 
                data_requirements, technical_requirements, context
            )
            
            logger.info(f"意图分析完成，置信度: {complete_intent.confidence_score:.2f}")
            return complete_intent
            
        except Exception as e:
            logger.error(f"意图分析失败: {e}", exc_info=True)
            return self._create_fallback_intent(query)
    
    async def _extract_basic_intent(self, query: str) -> Dict[str, Any]:
        """提取基础意图信息"""
        try:
            template = self.prompt_loader.load_template("basic_intent_extraction")
            prompt = template.format(query=query)
            
            response = await self.llm.ainvoke(prompt)
            result = self._parse_json_response(response.content)
            
            # 确保key使用英文
            return self._standardize_keys(result)
            
        except Exception as e:
            logger.warning(f"基础意图提取失败: {e}")
            return self._extract_basic_intent_fallback(query)
    
    async def _analyze_business_context(self, query: str, basic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析业务上下文"""
        try:
            template = self.prompt_loader.load_template("business_context_analysis")
            prompt = template.format(
                query=query,
                basic_analysis=json.dumps(basic_analysis, ensure_ascii=False, indent=2)
            )
            
            response = await self.llm.ainvoke(prompt)
            result = self._parse_json_response(response.content)
            
            # 标准化业务域和分析类型
            if "business_domain" in result:
                result["business_domain"] = self._standardize_business_domain(result["business_domain"])
            if "analysis_type" in result:
                result["analysis_type"] = self._standardize_analysis_type(result["analysis_type"])
            
            return self._standardize_keys(result)
            
        except Exception as e:
            logger.warning(f"业务上下文分析失败: {e}")
            return self._get_default_business_context()
    
    async def _analyze_data_requirements(self, query: str, business_context: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据需求"""
        try:
            # 获取可用的数据源信息
            available_tables = await self._get_available_data_sources()
            
            template = self.prompt_loader.load_template("data_requirements_analysis")
            prompt = template.format(
                query=query,
                business_context=json.dumps(business_context, ensure_ascii=False),
                available_tables=json.dumps(available_tables, ensure_ascii=False)
            )
            
            response = await self.llm.ainvoke(prompt)
            result = self._parse_json_response(response.content)
            
            # 验证和映射实体
            result = self._validate_entities(result, available_tables)
            
            return self._standardize_keys(result)
            
        except Exception as e:
            logger.warning(f"数据需求分析失败: {e}")
            return self._get_default_data_requirements()
    
    async def _analyze_technical_requirements(self, query: str, data_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析技术需求"""
        try:
            template = self.prompt_loader.load_template("technical_requirements_analysis")
            prompt = template.format(
                query=query,
                data_requirements=json.dumps(data_requirements, ensure_ascii=False)
            )
            
            response = await self.llm.ainvoke(prompt)
            result = self._parse_json_response(response.content)
            
            return self._standardize_keys(result)
            
        except Exception as e:
            logger.warning(f"技术需求分析失败: {e}")
            return self._get_default_technical_requirements()
    
    async def _get_available_data_sources(self) -> Dict[str, Any]:
        """获取可用的数据源信息"""
        try:
            # 首先尝试从MindsDB获取实时信息
            tables_info = {}
            
            for database in ["htinfo_db", "ext_ref_db"]:
                for table_name in self._get_table_names_for_database(database):
                    try:
                        metadata = await self.mindsdb_tool.get_table_metadata(database, table_name)
                        if metadata.get("success"):
                            tables_info[f"{database}.{table_name}"] = {
                                "database": database,
                                "table": table_name,
                                "columns": metadata.get("columns", []),
                                "record_count": metadata.get("record_count", 0),
                                "sample_data": metadata.get("sample_data", [])
                            }
                    except Exception as e:
                        logger.warning(f"获取表 {database}.{table_name} 信息失败: {e}")
            
            # 如果MindsDB获取失败，使用配置文件信息
            if not tables_info:
                schema = self._get_database_schema()
                tables_info = self._convert_schema_to_table_info(schema)
            
            return tables_info
            
        except Exception as e:
            logger.error(f"获取数据源信息失败: {e}")
            return self._get_default_table_info()
    
    def _get_table_names_for_database(self, database: str) -> List[str]:
        """获取指定数据库的表名列表"""
        schema = self._get_database_schema()
        return list(schema.get(database, {}).keys())
    
    def _convert_schema_to_table_info(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """将schema配置转换为表信息格式"""
        tables_info = {}
        for db_name, tables in schema.items():
            for table_name, table_info in tables.items():
                tables_info[f"{db_name}.{table_name}"] = {
                    "database": db_name,
                    "table": table_name,
                    "description": table_info.get("description", ""),
                    "key_fields": table_info.get("key_fields", [])
                }
        return tables_info
    
    def _synthesize_intent(self, query: str, basic_analysis: Dict[str, Any],
                          business_context: Dict[str, Any], data_requirements: Dict[str, Any],
                          technical_requirements: Dict[str, Any], context: Optional[Dict[str, Any]]) -> DataAnalysisIntent:
        """综合所有分析结果，形成完整的数据分析意图"""
        
        # 计算置信度
        confidence_score = self._calculate_confidence_score(
            basic_analysis, business_context, data_requirements, technical_requirements
        )
        
        return DataAnalysisIntent(
            # 核心意图
            business_objective=business_context.get("business_objective", "数据分析"),
            business_domain=business_context.get("business_domain", "general"),
            analysis_type=business_context.get("analysis_type", "descriptive"),
            
            # 数据需求
            primary_entities=data_requirements.get("primary_entities", []),
            secondary_entities=data_requirements.get("secondary_entities", []),
            analysis_dimensions=data_requirements.get("analysis_dimensions", []),
            target_metrics=data_requirements.get("target_metrics", []),
            
            # 分析要求
            time_range=data_requirements.get("time_range"),
            filter_conditions=data_requirements.get("filter_conditions", []),
            data_relationships=data_requirements.get("data_relationships", []),
            
            # 输出要求
            expected_insights=business_context.get("expected_insights", []),
            visualization_needs=data_requirements.get("visualization_needs", []),
            report_format="comprehensive",
            
            # 技术要求
            data_quality_requirements=data_requirements.get("data_quality_requirements", []),
            performance_requirements=technical_requirements.get("performance_requirements", {}),
            
            # 元数据
            confidence_score=confidence_score,
            complexity_level=technical_requirements.get("complexity_level", "medium"),
            estimated_execution_time=technical_requirements.get("estimated_execution_time", "2-5分钟")
        )
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM返回的JSON响应"""
        try:
            # 清理响应文本
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            return {"error": "json_parse_failed", "raw_response": response_text}
    
    def _standardize_keys(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """确保字典的key使用英文"""
        # 这里可以添加key标准化逻辑
        # 目前假设LLM已经返回英文key
        return data
    
    def _standardize_business_domain(self, domain_text: str) -> str:
        """标准化业务领域"""
        domain_mapping = {
            "零售": "retail",
            "电商": "ecommerce",
            "金融": "finance", 
            "营销": "marketing",
            "运营": "operations"
        }
        
        for key, value in domain_mapping.items():
            if key in domain_text.lower():
                return value
        
        return "general"
    
    def _standardize_analysis_type(self, type_text: str) -> str:
        """标准化分析类型"""
        type_mapping = {
            "描述": "descriptive",
            "诊断": "diagnostic",
            "预测": "predictive",
            "处方": "prescriptive",
            "趋势": "descriptive"
        }
        
        for key, value in type_mapping.items():
            if key in type_text:
                return value
        
        return "descriptive"
    
    def _validate_entities(self, requirements: Dict[str, Any], available_tables: Dict[str, Any]) -> Dict[str, Any]:
        """验证实体引用的表是否存在"""
        # 验证主要实体
        if "primary_entities" in requirements:
            validated_entities = []
            for entity in requirements["primary_entities"]:
                if isinstance(entity, dict) and "table_name" in entity:
                    table_key = f"{entity.get('database', 'htinfo_db')}.{entity['table_name']}"
                    if table_key in available_tables:
                        validated_entities.append(entity)
                    else:
                        logger.warning(f"表 {table_key} 不存在，跳过实体")
            requirements["primary_entities"] = validated_entities
        
        return requirements
    
    def _calculate_confidence_score(self, basic_analysis: Dict[str, Any], business_context: Dict[str, Any],
                                  data_requirements: Dict[str, Any], technical_requirements: Dict[str, Any]) -> float:
        """计算意图识别置信度"""
        score = 0.0
        
        # 基础分析质量 (25%)
        if basic_analysis.get("main_keywords") or basic_analysis.get("action_words"):
            score += 0.25
        
        # 业务上下文清晰度 (35%)
        if business_context.get("business_objective"):
            score += 0.2
        if business_context.get("business_domain") != "general":
            score += 0.15
        
        # 数据需求明确性 (30%)
        if data_requirements.get("primary_entities"):
            score += 0.15
        if data_requirements.get("target_metrics"):
            score += 0.15
        
        # 技术需求合理性 (10%)
        if technical_requirements.get("complexity_level"):
            score += 0.1
        
        return min(score, 1.0)
    
    # 备用方法
    def _extract_basic_intent_fallback(self, query: str) -> Dict[str, Any]:
        """基础意图提取的备用方法"""
        return {
            "main_keywords": [],
            "action_words": [],
            "data_objects": [],
            "extraction_method": "fallback"
        }
    
    def _get_default_business_context(self) -> Dict[str, Any]:
        """默认业务上下文"""
        return {
            "business_objective": "数据分析",
            "business_domain": "general",
            "analysis_type": "descriptive"
        }
    
    def _get_default_data_requirements(self) -> Dict[str, Any]:
        """默认数据需求"""
        return {
            "primary_entities": [],
            "target_metrics": [{"name": "总数", "type": "count"}]
        }
    
    def _get_default_technical_requirements(self) -> Dict[str, Any]:
        """默认技术需求"""
        return {
            "complexity_level": "medium",
            "estimated_execution_time": "2-5分钟"
        }
    
    def _get_default_table_info(self) -> Dict[str, Any]:
        """默认表信息"""
        return {
            "htinfo_db.walmart_orders": {
                "database": "htinfo_db",
                "table": "walmart_orders",
                "description": "沃尔玛订单数据"
            },
            "htinfo_db.walmart_online_item": {
                "database": "htinfo_db",
                "table": "walmart_online_item", 
                "description": "沃尔玛商品数据"
            }
        }
    
    def _create_fallback_intent(self, query: str) -> DataAnalysisIntent:
        """创建备用意图"""
        return DataAnalysisIntent(
            business_objective="数据查询和基础分析",
            business_domain="general",
            analysis_type="descriptive",
            primary_entities=[],
            secondary_entities=[],
            analysis_dimensions=[],
            target_metrics=[],
            time_range=None,
            filter_conditions=[],
            data_relationships=[],
            expected_insights=["基础统计信息"],
            visualization_needs=["表格"],
            report_format="basic",
            data_quality_requirements=[],
            performance_requirements={},
            confidence_score=0.3,
            complexity_level="low",
            estimated_execution_time="1-2分钟"
        )