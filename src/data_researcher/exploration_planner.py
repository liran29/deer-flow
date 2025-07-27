"""
数据探索规划器 (Data Exploration Planner)

基于意图识别结果，制定多步骤数据探索和分析计划，
等同于deep-research中的planner，但专注于数据分析workflow。
"""

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from .intent_analyzer import DataAnalysisIntent, PromptTemplateLoader
from ..llms.llm import get_llm_by_type

logger = logging.getLogger(__name__)

# 获取当前文件所在目录
CURRENT_DIR = Path(__file__).parent


class StepType(Enum):
    """分析步骤类型枚举"""
    DATA_EXPLORATION = "data_exploration"
    DATA_CLEANING = "data_cleaning"
    FEATURE_ENGINEERING = "feature_engineering"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    DEEP_ANALYSIS = "deep_analysis"
    VISUALIZATION = "visualization"
    INSIGHT_EXTRACTION = "insight_extraction"
    REPORT_GENERATION = "report_generation"


class Priority(Enum):
    """优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"


@dataclass
class AnalysisStep:
    """分析步骤定义"""
    step_id: str
    step_name: str
    step_type: str
    description: str
    inputs: List[str]
    outputs: List[str]
    tools: List[str]
    estimated_time: str
    dependencies: List[str]
    parallel_possible: bool
    priority: str
    
    # 扩展属性
    agent_type: Optional[str] = None  # 指定执行的代理类型
    query_templates: Optional[List[str]] = None  # SQL查询模板
    validation_criteria: Optional[List[str]] = None  # 验证标准
    fallback_strategy: Optional[str] = None  # 失败时的备用策略


@dataclass
class ExecutionStrategy:
    """执行策略定义"""
    parallel_groups: List[List[str]]  # 可并行执行的步骤组
    critical_path: List[str]  # 关键路径
    optimization_notes: List[str]  # 优化建议


@dataclass
class RiskAssessment:
    """风险评估定义"""
    data_availability_risk: str
    complexity_risk: str
    performance_risk: str
    mitigation_strategies: List[str]


@dataclass
class DataAnalysisPlan:
    """完整的数据分析计划"""
    plan_id: str
    plan_name: str
    total_estimated_time: str
    complexity_assessment: str
    steps: List[AnalysisStep]
    execution_strategy: ExecutionStrategy
    risk_assessment: RiskAssessment
    success_criteria: List[str]
    
    # 元数据
    created_from_intent: Optional[DataAnalysisIntent] = None
    plan_confidence: float = 0.0
    estimated_tokens: int = 0


class StepTemplateLibrary:
    """步骤模板库"""
    
    def __init__(self):
        self.templates = self._load_step_templates()
    
    def _load_step_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载预定义的步骤模板"""
        return {
            # 数据探索模板
            "basic_data_exploration": {
                "step_type": "data_exploration",
                "tools": ["MindsDBQueryTool", "DataProfilingTool"],
                "estimated_time": "2-3分钟",
                "priority": "high",
                "query_templates": [
                    "SELECT COUNT(*) as total_records FROM {table}",
                    "SELECT MIN({date_field}), MAX({date_field}) FROM {table}",
                    "SELECT COUNT(DISTINCT {key_field}) as unique_count FROM {table}"
                ]
            },
            
            # 趋势分析模板
            "time_series_analysis": {
                "step_type": "deep_analysis", 
                "tools": ["TimeSeriesAnalysisTool", "TrendCalculatorTool"],
                "estimated_time": "5-8分钟",
                "priority": "high",
                "query_templates": [
                    "SELECT DATE_FORMAT({date_field}, '%Y-%m') as period, COUNT(*) as count FROM {table} GROUP BY period ORDER BY period",
                    "SELECT DATE_FORMAT({date_field}, '%Y-%m') as period, SUM({amount_field}) as total FROM {table} GROUP BY period ORDER BY period"
                ]
            },
            
            # 分类统计模板
            "categorical_analysis": {
                "step_type": "statistical_analysis",
                "tools": ["StatisticalAnalysisTool", "CategoryAnalyzerTool"], 
                "estimated_time": "3-5分钟",
                "priority": "medium",
                "query_templates": [
                    "SELECT {category_field}, COUNT(*) as count FROM {table} GROUP BY {category_field} ORDER BY count DESC",
                    "SELECT {category_field}, AVG({numeric_field}) as avg_value FROM {table} GROUP BY {category_field}"
                ]
            },
            
            # 数据清洗模板
            "data_quality_check": {
                "step_type": "data_cleaning",
                "tools": ["DataQualityTool", "CleaningTool"],
                "estimated_time": "3-5分钟", 
                "priority": "high",
                "query_templates": [
                    "SELECT COUNT(*) as null_count FROM {table} WHERE {field} IS NULL",
                    "SELECT {field}, COUNT(*) as freq FROM {table} GROUP BY {field} HAVING COUNT(*) > 1"
                ]
            }
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """获取指定的步骤模板"""
        return self.templates.get(template_name, {})
    
    def get_templates_by_type(self, step_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的所有模板"""
        return [template for template in self.templates.values() 
                if template.get("step_type") == step_type]


class DataExplorationPlanner:
    """
    数据探索规划器
    
    基于数据分析意图，制定详细的多步骤数据探索和分析计划。
    类似于deep-research中的planner，但专注于数据分析领域。
    """
    
    def __init__(self):
        self.llm = None
        self.prompt_loader = PromptTemplateLoader(CURRENT_DIR / "prompts")
        self.step_library = StepTemplateLibrary()
        
        # 复杂度映射
        self.complexity_mapping = {
            "low": {"max_steps": 5, "max_time_minutes": 10},
            "medium": {"max_steps": 10, "max_time_minutes": 25},
            "high": {"max_steps": 15, "max_time_minutes": 45}
        }
    
    async def _ensure_dependencies(self):
        """确保依赖组件已初始化"""
        if self.llm is None:
            self.llm = get_llm_by_type("basic")
    
    async def create_analysis_plan(self, intent: DataAnalysisIntent, 
                                 constraints: Optional[Dict[str, Any]] = None) -> DataAnalysisPlan:
        """
        创建数据分析计划
        
        Args:
            intent: 数据分析意图
            constraints: 可选的约束条件（时间限制、资源限制等）
            
        Returns:
            DataAnalysisPlan: 完整的数据分析计划
        """
        await self._ensure_dependencies()
        
        try:
            logger.info(f"开始制定数据分析计划: {intent.business_objective}")
            
            # 1. 基于意图生成初步计划
            raw_plan = await self._generate_raw_plan(intent, constraints)
            
            # 2. 优化和完善计划
            optimized_plan = await self._optimize_plan(raw_plan, intent, constraints)
            
            # 3. 验证计划的可行性
            validated_plan = await self._validate_plan(optimized_plan, intent)
            
            # 4. 生成执行策略
            execution_strategy = self._generate_execution_strategy(validated_plan)
            
            # 5. 评估风险
            risk_assessment = self._assess_risks(validated_plan, intent)
            
            # 6. 构建完整计划
            complete_plan = self._build_complete_plan(
                validated_plan, execution_strategy, risk_assessment, intent
            )
            
            logger.info(f"计划制定完成，包含 {len(complete_plan.steps)} 个步骤")
            return complete_plan
            
        except Exception as e:
            logger.error(f"计划制定失败: {e}", exc_info=True)
            return self._create_fallback_plan(intent)
    
    async def _generate_raw_plan(self, intent: DataAnalysisIntent, 
                               constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """生成初步的分析计划"""
        try:
            template = self.prompt_loader.load_template("exploration_plan_generation")
            
            # 准备模板变量
            template_vars = {
                "business_objective": intent.business_objective,
                "business_domain": intent.business_domain,
                "analysis_type": intent.analysis_type,
                "primary_entities": json.dumps(intent.primary_entities, ensure_ascii=False),
                "target_metrics": json.dumps(intent.target_metrics, ensure_ascii=False),
                "analysis_dimensions": json.dumps(intent.analysis_dimensions, ensure_ascii=False),
                "complexity_level": intent.complexity_level
            }
            
            # 添加约束信息
            if constraints:
                template_vars["constraints"] = json.dumps(constraints, ensure_ascii=False)
            
            prompt = template.format(**template_vars)
            
            response = await self.llm.ainvoke(prompt)
            raw_plan = self._parse_json_response(response.content)
            
            return raw_plan
            
        except Exception as e:
            logger.warning(f"生成原始计划失败: {e}")
            return self._generate_template_based_plan(intent)
    
    def _generate_template_based_plan(self, intent: DataAnalysisIntent) -> Dict[str, Any]:
        """基于模板生成备用计划"""
        steps = []
        step_counter = 1
        
        # 1. 数据探索步骤
        if intent.primary_entities:
            for entity in intent.primary_entities:
                if isinstance(entity, dict) and "table_name" in entity:
                    template = self.step_library.get_template("basic_data_exploration")
                    step = {
                        "step_id": f"explore_{step_counter:03d}",
                        "step_name": f"探索{entity.get('name', '数据')}",
                        "step_type": template["step_type"],
                        "description": f"分析{entity.get('table_name')}表的基础信息",
                        "inputs": [f"{entity.get('table_name')}表访问权限"],
                        "outputs": ["数据概览报告"],
                        "tools": template["tools"],
                        "estimated_time": template["estimated_time"],
                        "dependencies": [],
                        "parallel_possible": True,
                        "priority": template["priority"]
                    }
                    steps.append(step)
                    step_counter += 1
        
        # 2. 基于分析类型添加特定步骤
        if intent.analysis_type == "descriptive":
            # 添加趋势分析步骤
            if any("时间" in dim.get("name", "") for dim in intent.analysis_dimensions):
                template = self.step_library.get_template("time_series_analysis")
                steps.append({
                    "step_id": f"analysis_{step_counter:03d}",
                    "step_name": "时间趋势分析",
                    "step_type": template["step_type"],
                    "description": "分析数据的时间变化趋势",
                    "inputs": ["清洗后的数据"],
                    "outputs": ["趋势分析结果"],
                    "tools": template["tools"],
                    "estimated_time": template["estimated_time"],
                    "dependencies": [steps[0]["step_id"]] if steps else [],
                    "parallel_possible": False,
                    "priority": template["priority"]
                })
                step_counter += 1
        
        return {
            "plan_id": f"template_plan_{hash(intent.business_objective) % 10000}",
            "plan_name": f"{intent.business_objective} - 模板计划",
            "steps": steps,
            "total_estimated_time": "10-15分钟",
            "complexity_assessment": intent.complexity_level
        }
    
    async def _optimize_plan(self, raw_plan: Dict[str, Any], intent: DataAnalysisIntent,
                           constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """优化分析计划"""
        # 检查步骤数量是否合理
        complexity_limits = self.complexity_mapping.get(intent.complexity_level, 
                                                       self.complexity_mapping["medium"])
        
        steps = raw_plan.get("steps", [])
        if len(steps) > complexity_limits["max_steps"]:
            # 保留高优先级步骤
            high_priority_steps = [s for s in steps if s.get("priority") == "high"]
            medium_priority_steps = [s for s in steps if s.get("priority") == "medium"]
            
            # 重新组合步骤
            optimized_steps = high_priority_steps
            remaining_slots = complexity_limits["max_steps"] - len(high_priority_steps)
            if remaining_slots > 0:
                optimized_steps.extend(medium_priority_steps[:remaining_slots])
            
            raw_plan["steps"] = optimized_steps
            logger.info(f"计划优化：从 {len(steps)} 个步骤减少到 {len(optimized_steps)} 个")
        
        return raw_plan
    
    async def _validate_plan(self, plan: Dict[str, Any], intent: DataAnalysisIntent) -> Dict[str, Any]:
        """验证计划的可行性"""
        steps = plan.get("steps", [])
        
        # 验证依赖关系
        step_ids = {step["step_id"] for step in steps}
        for step in steps:
            dependencies = step.get("dependencies", [])
            for dep in dependencies:
                if dep not in step_ids:
                    logger.warning(f"步骤 {step['step_id']} 的依赖 {dep} 不存在")
                    step["dependencies"] = [d for d in dependencies if d in step_ids]
        
        # 验证工具可用性
        available_tools = self._get_available_tools()
        for step in steps:
            step_tools = step.get("tools", [])
            unavailable_tools = [tool for tool in step_tools if tool not in available_tools]
            if unavailable_tools:
                logger.warning(f"步骤 {step['step_id']} 包含不可用的工具: {unavailable_tools}")
                # 替换为可用工具
                step["tools"] = [tool for tool in step_tools if tool in available_tools]
                if not step["tools"]:
                    step["tools"] = ["MindsDBQueryTool"]  # 默认工具
        
        return plan
    
    def _generate_execution_strategy(self, plan: Dict[str, Any]) -> ExecutionStrategy:
        """生成执行策略"""
        steps = plan.get("steps", [])
        
        # 分析并行可能性
        parallel_groups = []
        current_group = []
        
        for step in steps:
            if step.get("parallel_possible", False) and not step.get("dependencies"):
                current_group.append(step["step_id"])
            else:
                if current_group:
                    parallel_groups.append(current_group)
                    current_group = []
                parallel_groups.append([step["step_id"]])
        
        if current_group:
            parallel_groups.append(current_group)
        
        # 识别关键路径
        critical_path = []
        for step in steps:
            if step.get("priority") == "high":
                critical_path.append(step["step_id"])
        
        return ExecutionStrategy(
            parallel_groups=parallel_groups,
            critical_path=critical_path,
            optimization_notes=[
                "高优先级步骤优先执行",
                "无依赖步骤可并行处理",
                "可视化步骤可与分析并行"
            ]
        )
    
    def _assess_risks(self, plan: Dict[str, Any], intent: DataAnalysisIntent) -> RiskAssessment:
        """评估计划风险"""
        steps = plan.get("steps", [])
        
        # 数据可用性风险
        data_risk = "low"
        if not intent.primary_entities:
            data_risk = "high"
        elif len(intent.primary_entities) > 3:
            data_risk = "medium"
        
        # 复杂度风险
        complexity_risk = "low"
        if len(steps) > 10:
            complexity_risk = "high"
        elif len(steps) > 6:
            complexity_risk = "medium"
        
        # 性能风险
        performance_risk = "low"
        if intent.complexity_level == "high":
            performance_risk = "medium"
        
        return RiskAssessment(
            data_availability_risk=data_risk,
            complexity_risk=complexity_risk,
            performance_risk=performance_risk,
            mitigation_strategies=[
                "增加数据验证步骤",
                "分批处理大数据集",
                "设置超时和重试机制"
            ]
        )
    
    def _build_complete_plan(self, plan: Dict[str, Any], execution_strategy: ExecutionStrategy,
                           risk_assessment: RiskAssessment, intent: DataAnalysisIntent) -> DataAnalysisPlan:
        """构建完整的分析计划"""
        
        # 转换步骤为AnalysisStep对象
        analysis_steps = []
        for step_data in plan.get("steps", []):
            step = AnalysisStep(
                step_id=step_data.get("step_id", ""),
                step_name=step_data.get("step_name", ""),
                step_type=step_data.get("step_type", ""),
                description=step_data.get("description", ""),
                inputs=step_data.get("inputs", []),
                outputs=step_data.get("outputs", []),
                tools=step_data.get("tools", []),
                estimated_time=step_data.get("estimated_time", ""),
                dependencies=step_data.get("dependencies", []),
                parallel_possible=step_data.get("parallel_possible", False),
                priority=step_data.get("priority", "medium")
            )
            analysis_steps.append(step)
        
        return DataAnalysisPlan(
            plan_id=plan.get("plan_id", f"plan_{hash(intent.business_objective) % 10000}"),
            plan_name=plan.get("plan_name", intent.business_objective),
            total_estimated_time=plan.get("total_estimated_time", "15-25分钟"),
            complexity_assessment=plan.get("complexity_assessment", intent.complexity_level),
            steps=analysis_steps,
            execution_strategy=execution_strategy,
            risk_assessment=risk_assessment,
            success_criteria=plan.get("success_criteria", [
                "完成所有预定指标的计算",
                "生成关键业务洞察",
                "创建可视化图表",
                "形成完整的分析报告"
            ]),
            created_from_intent=intent,
            plan_confidence=intent.confidence_score
        )
    
    def _get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return [
            "MindsDBQueryTool",
            "DataProfilingTool", 
            "DataQualityTool",
            "StatisticalAnalysisTool",
            "TimeSeriesAnalysisTool",
            "VisualizationTool",
            "ReportGeneratorTool"
        ]
    
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
    
    def _create_fallback_plan(self, intent: DataAnalysisIntent) -> DataAnalysisPlan:
        """创建备用分析计划"""
        fallback_steps = [
            AnalysisStep(
                step_id="fallback_001",
                step_name="基础数据查询",
                step_type="data_exploration",
                description="执行基础的数据查询和统计",
                inputs=["数据库访问权限"],
                outputs=["基础统计结果"],
                tools=["MindsDBQueryTool"],
                estimated_time="3-5分钟",
                dependencies=[],
                parallel_possible=True,
                priority="high"
            )
        ]
        
        return DataAnalysisPlan(
            plan_id="fallback_plan",
            plan_name=f"{intent.business_objective} - 备用计划",
            total_estimated_time="5-10分钟",
            complexity_assessment="low",
            steps=fallback_steps,
            execution_strategy=ExecutionStrategy(
                parallel_groups=[["fallback_001"]],
                critical_path=["fallback_001"],
                optimization_notes=["简化执行策略"]
            ),
            risk_assessment=RiskAssessment(
                data_availability_risk="medium",
                complexity_risk="low",
                performance_risk="low",
                mitigation_strategies=["使用基础查询工具"]
            ),
            success_criteria=["完成基础数据查询"],
            created_from_intent=intent,
            plan_confidence=0.3
        )