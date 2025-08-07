import logging
import json
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.config.database_schema_manager import get_database_schema_manager
from src.config.configuration import Configuration
from src.llms.llm import get_llm_by_type
from src.prompts.template import apply_prompt_template
from src.utils.json_utils import repair_json_output
from src.agents import create_agent
from src.tools.mindsdb_mcp import mindsdb_query_tool, mindsdb_table_info_tool

from .types import State
from src.prompts.planner_model import Plan, QueryStrategy, ResultSize

logger = logging.getLogger(__name__)


def _get_strategy_guidance(step) -> str:
    """Generate execution guidance based on query strategy"""
    import os
    from jinja2 import Template
    
    strategy = getattr(step, 'query_strategy', QueryStrategy.AGGREGATION)
    justification = getattr(step, 'justification', '')
    batch_size = getattr(step, 'batch_size', None)
    expected_size = getattr(step, 'expected_result_size', ResultSize.SMALL_SET)
    
    # Load strategy guidance from prompt file
    strategy_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "prompts", 
        "database_query_strategy.md"
    )
    
    try:
        with open(strategy_file, 'r', encoding='utf-8') as f:
            strategy_template = f.read()
        
        # Create context for template rendering
        context = {
            'strategy': strategy.value,
            'justification': justification,
            'expected_size': expected_size.value,
            'batch_size': batch_size or 20
        }
        
        # Render template with context
        template = Template(strategy_template)
        rendered_guidance = template.render(**context)
        
        # Add strategy-specific header
        header = f"**Query Strategy**: {strategy.value}\n**Justification**: {justification}\n**Expected Result Size**: {expected_size.value}\n\n"
        
        return header + rendered_guidance
        
    except Exception as e:
        logger.error(f"Failed to load strategy guidance: {str(e)}")
        # Fallback to minimal guidance
        return f"**Query Strategy**: {strategy.value}\n**Justification**: {justification}\nPlease use appropriate SQL patterns for {strategy.value} strategy."


def _analyze_execution_result(step, execution_result: str) -> dict:
    """Analyze execution result efficiency"""
    analysis = {
        "is_efficient": True,
        "warnings": [],
        "suggestions": [],
        "data_volume_estimate": "unknown"
    }
    
    # 检查是否返回了大量数据的迹象
    large_data_indicators = [
        "Retrieved 100",
        "Retrieved 200", 
        "Retrieved 500",
        "Retrieved 1000",
        "rows.",
        "total_rows"
    ]
    
    if any(indicator in execution_result for indicator in large_data_indicators):
        analysis["is_efficient"] = False
        analysis["warnings"].append("查询可能返回了大量数据")
        
        strategy = getattr(step, 'query_strategy', QueryStrategy.AGGREGATION) 
        if strategy == QueryStrategy.AGGREGATION:
            analysis["suggestions"].append("聚合策略应该返回汇总数据，而非大量原始数据")
        elif strategy == QueryStrategy.SAMPLING:
            batch_size = getattr(step, 'batch_size', 20)
            analysis["suggestions"].append(f"采样策略应该限制在{batch_size}行以内")
    
    # 检查是否正确使用了聚合函数
    aggregation_indicators = ["COUNT", "SUM", "AVG", "GROUP BY", "统计", "总计", "平均"]
    if any(indicator in execution_result.upper() for indicator in aggregation_indicators):
        analysis["data_volume_estimate"] = "aggregated"
    elif "LIMIT" in execution_result.upper():
        analysis["data_volume_estimate"] = "limited"
    else:
        analysis["data_volume_estimate"] = "potentially_large"
    
    return analysis


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


async def database_investigation_node(state: State, config: RunnableConfig) -> Command[Literal["planner"]]:
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
            return Command(
                update={
                    "database_investigation_results": "",
                    "messages": [AIMessage(
                        content="__DB_INVESTIGATION_NO_DATABASE__",
                        name="background_investigator"
                    )]
                },
                goto="planner"
            )
        
        # 发送开始消息给前端
        start_message = AIMessage(
            content=f"__DB_INVESTIGATION_STARTING__|{query}",
            name="background_investigator"
        )
        logger.info(f"准备发送开始消息: {start_message.content}")
        
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
        
        # 提取数据库和表信息
        db_tables_info = []
        current_db = None
        tables = []
        
        for line in database_info.split('\n'):
            if 'Database:' in line:
                if current_db and tables:
                    db_tables_info.append(f"{current_db}: {', '.join(tables[:5])}" + ("..." if len(tables) > 5 else ""))
                current_db = line.split('Database:')[1].strip()
                tables = []
            elif '  - ' in line and current_db:
                table_name = line.strip().replace('- ', '')
                if '(' in table_name:
                    table_name = table_name.split('(')[0].strip()
                tables.append(table_name)
        
        # 添加最后一个数据库
        if current_db and tables:
            db_tables_info.append(f"{current_db}: {', '.join(tables[:5])}" + ("..." if len(tables) > 5 else ""))
        
        db_count = len(db_tables_info)
        db_tables_str = " | ".join(db_tables_info[:3]) + ("..." if len(db_tables_info) > 3 else "")
        
        # 创建完成消息
        completion_message = AIMessage(
            content=f"__DB_INVESTIGATION_COMPLETED__|{llm_analysis}|{db_count}|{db_tables_str}",
            name="background_investigator"
        )
        
        logger.info(f"数据库调查完成，结果长度: {len(investigation_results)} 字符")
        
        return Command(
            update={
                "database_investigation_results": investigation_results,
                "messages": [start_message, completion_message]
            },
            goto="planner"
        )
            
    except Exception as e:
        logger.error(f"Database investigation node failed: {str(e)}", exc_info=True)
        error_message = AIMessage(
            content=f"__DB_INVESTIGATION_FAILED__|{str(e)}",
            name="background_investigator"
        )
        return Command(
            update={
                "database_investigation_results": "",
                "messages": [error_message]
            },
            goto="planner"
        )


def database_planner_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """数据库分析计划节点 - 生成数据库查询和分析计划"""
    logger.info("数据库计划节点开始生成计划")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        
        # 获取调查结果作为背景信息
        investigation_results = state.get("database_investigation_results", "")
        if not investigation_results:
            logger.warning("缺少数据库调查结果，无法生成计划")
            return Command(goto="research_team")
        
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
            return Command(goto="research_team")
        
        if isinstance(curr_plan, dict):
            new_plan = Plan.model_validate(curr_plan)
            return Command(
                update={
                    "messages": [AIMessage(content=full_response, name="database_planner")],
                    "current_plan": new_plan,
                },
                goto="research_team",
            )
        
        return Command(goto="research_team")
        
    except Exception as e:
        logger.error(f"数据库计划节点失败: {str(e)}", exc_info=True)
        return Command(goto="research_team")


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


def database_research_team_node(state: State):
    """数据库研究团队节点 - 协调数据库查询步骤的执行"""
    logger.info("数据库研究团队开始协调任务执行")
    pass


async def _execute_database_agent_step(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """执行数据库分析步骤的辅助函数"""
    current_plan = state.get("current_plan")
    if not current_plan:
        logger.warning("缺少分析计划，无法执行步骤")
        return Command(goto="research_team")
    
    plan_title = current_plan.title
    observations = state.get("observations", [])

    # 找到第一个未执行的步骤
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        if not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.info("所有步骤已完成，条件路由将处理下一步")
        return Command(goto="research_team")

    logger.info(f"执行数据库分析步骤: {current_step.title}, 代理: {agent_name}")

    # 格式化已完成步骤的信息
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# Previously Completed Analysis Steps\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## Completed Step {i + 1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # 根据查询策略定制agent输入
    strategy_guidance = _get_strategy_guidance(current_step)
    
    # 为代理准备输入，包含已完成步骤信息和策略指导
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"# Database Analysis Topic\n\n{plan_title}\n\n{completed_steps_info}# Current Step\n\n## Title\n\n{current_step.title}\n\n## Description\n\n{current_step.description}\n\n## Query Strategy Guidance\n\n{strategy_guidance}\n\n## Language Setting\n\n{state.get('locale', 'zh-CN')}"
            )
        ]
    }

    try:
        # 调用代理执行步骤
        result = await agent.ainvoke(agent_input)
        execution_result = result["messages"][-1].content

        # 分析执行效率
        efficiency_analysis = _analyze_execution_result(current_step, execution_result)
        
        # 记录效率分析结果
        if not efficiency_analysis["is_efficient"]:
            logger.warning(f"步骤 '{current_step.title}' 执行效率预警: {efficiency_analysis['warnings']}")
            for suggestion in efficiency_analysis["suggestions"]:
                logger.info(f"优化建议: {suggestion}")
        
        logger.info(f"步骤 '{current_step.title}' 数据量估计: {efficiency_analysis['data_volume_estimate']}")

        # 更新步骤执行结果
        current_step.execution_res = execution_result
        
        # 添加到观察结果
        observations.append(f"步骤 '{current_step.title}' 执行完成 (策略: {getattr(current_step, 'query_strategy', 'unknown').value if hasattr(getattr(current_step, 'query_strategy', None), 'value') else 'unknown'})")

        return Command(
            update={
                "current_plan": current_plan,
                "observations": observations,
                "messages": state["messages"] + [AIMessage(content=execution_result, name=agent_name)]
            },
            goto="research_team"
        )

    except Exception as e:
        logger.error(f"执行数据库分析步骤失败: {str(e)}", exc_info=True)
        current_step.execution_res = f"步骤执行失败: {str(e)}"
        
        return Command(
            update={
                "current_plan": current_plan,
                "observations": observations + [f"步骤 '{current_step.title}' 执行失败"],
            },
            goto="research_team"
        )


async def database_researcher_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """数据库研究员节点 - 执行数据库查询和分析"""
    logger.info("数据库研究员开始执行查询分析")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        
        # 创建MindsDB工具列表
        tools = [mindsdb_query_tool, mindsdb_table_info_tool]
        
        # 创建数据库研究员代理
        database_researcher_agent = create_agent(
            agent_name="researcher",
            agent_type="researcher", 
            tools=tools,
            prompt_template="researcher"
        )
        
        logger.info(f"数据库研究员工具: {tools}")
        
        return await _execute_database_agent_step(
            state,
            database_researcher_agent,
            "researcher"
        )
        
    except Exception as e:
        logger.error(f"数据库研究员节点失败: {str(e)}", exc_info=True)
        return Command(goto="research_team")
