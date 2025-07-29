import logging
import json
from typing import Literal

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.config.database_schema_manager import get_database_schema_manager
from src.config.configuration import Configuration
from src.llms.llm import get_llm_by_type
from src.prompts.template import apply_prompt_template
from src.utils.json_utils import repair_json_output

from .types import State
from src.prompts.planner_model import Plan

logger = logging.getLogger(__name__)


def validate_llm_response(response_content: str) -> bool:
    """简单验证LLM响应是否有效"""
    
    if not response_content:
        return False
    
    # 检查响应长度
    if len(response_content.strip()) < 50:
        logger.warning("LLM响应过短")
        return False
    
    # 检查是否包含关键部分
    key_sections = ["Query Understanding", "Required Data Dimensions", "Suggested Analyses"]
    found_sections = sum(1 for section in key_sections if section in response_content)
    
    if found_sections < 2:
        logger.warning(f"LLM响应缺少关键部分，只找到 {found_sections}/{len(key_sections)} 个部分")
        return False
    
    return True


async def analyze_query_with_database_info(query: str, database_info: str, configurable) -> str:
    """使用LLM分析查询和数据库信息，返回分析建议"""
    
    try:
        # 创建临时状态用于模板渲染
        temp_state = {
            "messages": [],
            "query": query,
            "database_info": database_info
        }
        
        # 应用提示词模板
        messages = apply_prompt_template("database_investigation", temp_state, configurable)
        
        # 获取LLM（使用basic模型以保持一致性）
        llm = get_llm_by_type("basic")
        
        # 调用LLM
        logger.info("调用LLM分析数据库查询维度...")
        response = await llm.ainvoke(messages)
        
        # 验证响应
        if validate_llm_response(response.content):
            return response.content
        else:
            logger.warning("LLM响应验证失败，返回默认分析")
            return f"基于查询 '{query}'，建议分析可用数据库中的相关数据。"
        
    except Exception as e:
        logger.error(f"LLM分析失败: {str(e)}")
        return f"无法生成详细分析建议。查询: {query}"


async def database_investigation_node(state: State, config: RunnableConfig):
    """数据库调查节点 - 使用LLM分析用户查询并提取数据分析维度"""
    logger.info("Database investigation node is running.")
    
    try:
        query = state.get("research_topic")
        logger.info(f"数据库调查主题: {query}")
        
        # 获取配置管理器并获取数据库信息
        schema_manager = get_database_schema_manager()
        database_info = await schema_manager.get_database_info()
        
        if not database_info:
            logger.warning("未获取到数据库信息")
            return {
                "database_investigation_results": ""
            }
        
        # 使用LLM分析查询和数据库信息
        configurable = Configuration.from_runnable_config(config)
        llm_analysis = await analyze_query_with_database_info(
            query, 
            database_info,
            configurable
        )
        
        # 组合结果：数据库信息 + LLM分析建议
        investigation_results = f"""# Database Investigation Report

## Data Analysis Dimension Recommendations
{llm_analysis}

## Available Database Information
{database_info}"""
        
        logger.info(f"数据库调查完成，结果长度: {len(investigation_results)} 字符")
        
        return {
            "database_investigation_results": investigation_results
        }
            
    except Exception as e:
        logger.error(f"Database investigation node failed: {str(e)}", exc_info=True)
        return {
            "database_investigation_results": ""
        }


def database_planner_node(
    state: State, config: RunnableConfig
) -> Command[Literal["database_reporter"]]:
    """数据库分析计划节点 - 生成数据库查询和分析计划"""
    logger.info("数据库计划节点开始生成计划")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        
        # 获取调查结果作为背景信息
        investigation_results = state.get("database_investigation_results", "")
        if not investigation_results:
            logger.warning("缺少数据库调查结果，无法生成计划")
            return Command(goto="database_reporter")
        
        # 准备LLM消息
        messages = apply_prompt_template("database_planner", state, configurable)
        
        # 添加数据库调查结果作为背景
        messages += [{
            "role": "user", 
            "content": f"{investigation_results}\n\nBased on the above database investigation results, please generate a comprehensive data analysis plan that leverages the available database resources to answer the user's query."
        }]
        
        # 使用structured output获取计划
        llm = get_llm_by_type("basic").with_structured_output(
            Plan,
            method="json_mode",
        )
        
        response = llm.invoke(messages)
        full_response = response.model_dump_json(indent=4, exclude_none=True)
        
        logger.info(f"数据库计划生成完成: {full_response}")
        
        try:
            curr_plan = json.loads(repair_json_output(full_response))
        except json.JSONDecodeError:
            logger.warning("数据库计划响应不是有效的JSON")
            return Command(goto="database_reporter")
        
        if isinstance(curr_plan, dict):
            new_plan = Plan.model_validate(curr_plan)
            return Command(
                update={
                    "messages": [AIMessage(content=full_response, name="database_planner")],
                    "current_plan": new_plan,
                },
                goto="database_reporter",
            )
        
        return Command(goto="database_reporter")
        
    except Exception as e:
        logger.error(f"数据库计划节点失败: {str(e)}", exc_info=True)
        return Command(goto="database_reporter")


async def database_reporter_node(state: State, config: RunnableConfig):
    """数据库分析报告节点 - 生成最终的数据分析报告"""
    logger.info("数据库报告节点开始生成报告")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        
        # 获取计划和调查结果
        current_plan = state.get("current_plan")
        investigation_results = state.get("database_investigation_results", "")
        
        if not current_plan:
            logger.warning("缺少分析计划，无法生成报告")
            return {
                "final_report": "数据库分析失败：缺少分析计划",
                "messages": [AIMessage(content="数据库分析失败：缺少分析计划")]
            }
        
        # 准备LLM消息
        messages = apply_prompt_template("database_reporter", state, configurable)
        
        # 添加计划和调查结果作为背景
        plan_json = current_plan.model_dump_json(indent=2) if hasattr(current_plan, 'model_dump_json') else str(current_plan)
        messages += [{
            "role": "user", 
            "content": f"""Database Analysis Context:

{investigation_results}

Generated Analysis Plan:
{plan_json}

Based on the above database investigation results and analysis plan, please generate a comprehensive data analysis report that addresses the user's query using the available database resources."""
        }]
        
        # 获取LLM生成报告
        llm = get_llm_by_type("basic")
        
        response = llm.invoke(messages)
        final_report = response.content
        
        logger.info(f"数据库分析报告生成完成，报告长度: {len(final_report)} 字符")
        
        return {
            "final_report": final_report,
            "messages": [AIMessage(content=final_report, name="database_reporter")]
        }
        
    except Exception as e:
        logger.error(f"数据库报告节点失败: {str(e)}", exc_info=True)
        error_message = f"数据库分析报告生成失败: {str(e)}"
        return {
            "final_report": error_message,
            "messages": [AIMessage(content=error_message)]
        }
