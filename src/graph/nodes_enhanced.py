# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Enhanced nodes for step dependency optimization.

This module contains enhanced versions of the original nodes that implement
token optimization through smart dependency management.
"""

import asyncio
import json
import logging
import os
import time
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.agents import create_agent
from src.tools.search import LoggedTavilySearch
from src.tools import (
    crawl_tool,
    get_web_search_tool,
    get_retriever_tool,
    python_repl_tool,
)
from src.tools.mindsdb_mcp import MindsDBMCPTool
from src.config.mindsdb_mcp import MindsDBMCPConfig

from src.config.agents import AGENT_LLM_MAP
from src.config.configuration import Configuration
from src.llms.llm import get_llm_by_type
from src.prompts.planner_model import Plan, ExecutionStatus
from src.prompts.template import apply_prompt_template
from src.utils.json_utils import repair_json_output

from .nodes import (
    background_investigation_node,
)

from .types import State
from ..config import SELECTED_SEARCH_ENGINE, SearchEngine
from ..utils.search_summarizer import llm_summarize_search_result, format_summarized_result
from ..utils.enhanced_features import is_mindsdb_database_integration_enabled

logger = logging.getLogger(__name__)


async def database_query_node(state: State, config: RunnableConfig):
    """专门的数据库查询节点 - 从MindsDB获取相关数据"""
    logger.info("Database query node is running.")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        query = state.get("research_topic")
        logger.info(f"数据库查询主题: {query}")
        
        # 初始化MindsDB工具和配置
        mindsdb_tool = MindsDBMCPTool()
        mindsdb_config = MindsDBMCPConfig.load_from_file()
        
        database_results = ""
        
        try:
            logger.info("开始从本地数据库获取相关信息...")
            available_databases = mindsdb_tool.get_available_databases()
            logger.info(f"可用数据库: {available_databases}")
            
            if available_databases:
                # 为每个数据库获取表信息和样本数据
                for db_name in available_databases:
                    table_info = await mindsdb_tool.get_table_info(db_name)
                    
                    if table_info.get("success"):
                        tables = [row[0] for row in table_info.get("data", [])]
                        logger.info(f"数据库 {db_name} 中的表: {tables}")
                        database_results += f"\n\n## 数据库 {db_name}\n可用表: {', '.join(tables)}\n"
                        
                        # 为每个表获取结构信息和少量样本数据
                        for table in tables[:3]:  # 限制最多3个表以避免过多数据
                            try:
                                # 获取表结构
                                structure_info = await mindsdb_tool.get_table_info(db_name, table)
                                if structure_info.get("success"):
                                    database_results += f"\n### 表 {table} 结构:\n"
                                    for row in structure_info.get("data", [])[:5]:  # 最多5个字段
                                        database_results += f"  - {row}\n"
                                
                                # 获取样本数据
                                sample_query = f"SELECT * FROM {db_name}.{table} LIMIT 2"
                                result = await mindsdb_tool.query_database(db_name, sample_query)
                                
                                if result.get("success") and result.get("data"):
                                    database_results += f"\n### 表 {table} 样本数据:\n"
                                    database_results += f"列名: {', '.join(result.get('columns', []))}\n"
                                    for i, row in enumerate(result.get('data', [])[:2]):
                                        database_results += f"  记录{i+1}: {row}\n"
                                        
                            except Exception as e:
                                logger.warning(f"查询表 {table} 失败: {str(e)}")
                                database_results += f"\n### 表 {table}: 查询失败 - {str(e)}\n"
                    else:
                        database_results += f"\n\n## 数据库 {db_name}: 无法获取表信息\n"
                        
            else:
                database_results = "未找到可用的数据库连接。请检查MindsDB配置。"
                
        except Exception as e:
            logger.error(f"数据库查询过程出错: {str(e)}")
            database_results = f"数据库查询失败: {str(e)}"
        
        if database_results:
            logger.info(f"数据库查询完成，结果长度: {len(database_results)} 字符")
            return {
                "database_query_results": database_results
            }
        else:
            return {
                "database_query_results": "未能从数据库获取任何信息。"
            }
            
    except Exception as e:
        logger.error(f"Database query node failed: {str(e)}", exc_info=True)
        return {
            "database_query_results": f"数据库查询节点执行失败: {str(e)}"
        }


async def background_investigation_node_enhanced(state: State, config: RunnableConfig):
    """增强版背景调查节点 - 使用LLM智能摘要压缩搜索结果，可选集成数据库查询"""
    logger.info("Enhanced background investigation node is running.")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        query = state.get("research_topic")
        logger.info(f"State中的所有字段: {list(state.keys())}")
        logger.info(f"研究主题: {query}")
        logger.info(f"研究主题类型: {type(query)}")
        
        # 检查是否启用了MindsDB数据库集成
        database_results = ""
        if is_mindsdb_database_integration_enabled():
            try:
                logger.info("MindsDB数据库集成已启用，开始查询本地数据库...")
                
                # 直接调用数据库查询节点（现在都是async函数）
                db_result = await database_query_node(state, config)
                if db_result and "database_query_results" in db_result:
                    database_results = db_result["database_query_results"]
                    logger.info(f"数据库查询结果长度: {len(database_results)} 字符")
                    
            except ImportError:
                logger.warning("MindsDB工具未找到，跳过数据库查询")
            except Exception as e:
                logger.warning(f"数据库查询失败: {str(e)}")
        
        if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
            # 增加搜索结果数量以获得更全面的信息
            search_results_count = max(8, configurable.max_search_results)
            logger.info(f"搜索结果数量: {search_results_count}")
            
            searched_content = LoggedTavilySearch(
                max_results=search_results_count,
                include_raw_content=True,
                include_images=True,
            ).invoke(query)
            
            if isinstance(searched_content, list):
                logger.info(f"开始对 {len(searched_content)} 个搜索结果进行LLM摘要...")
                
                # 对每个搜索结果使用LLM进行智能摘要
                compressed_results = []
                for i, elem in enumerate(searched_content):
                    logger.info(f"正在摘要第 {i+1}/{len(searched_content)} 个结果: {elem.get('title', '')[:50]}...")
                    
                    # 添加延迟以避免API速率限制（除第一个请求外）
                    if i > 0:
                        logger.info(f"等待20秒以避免API速率限制...")
                        time.sleep(2)  # Moonshot API限制每分钟3个请求，即20秒一个请求
                    
                    # 使用LLM生成摘要
                    summary_result = llm_summarize_search_result(elem, query)
                    
                    # 检查是否为有效内容
                    if not summary_result.get("is_valid", True):
                        logger.info(f"跳过无效内容: {elem.get('title', '')[:50]}... 原因: {summary_result.get('reason', '')}")
                        continue
                    
                    # 格式化摘要结果
                    summary_text = summary_result.get("summary", "")
                    formatted_result = format_summarized_result(elem, summary_text)
                    compressed_results.append(formatted_result)
                
                logger.info("LLM摘要完成，返回压缩后的结果")
                web_search_result = "\n\n".join(compressed_results)
                logger.info(f"Web搜索摘要结果长度: {len(web_search_result)} 字符")
                logger.debug(f"Web搜索摘要结果预览: {web_search_result[:300]}...")
                
                # 整合数据库查询结果和Web搜索结果
                final_result_parts = []
                if database_results and database_results.strip():
                    final_result_parts.append(f"**数据库查询结果:**\n{database_results}")
                    logger.info("已添加数据库查询结果到最终输出")
                
                if web_search_result and web_search_result.strip():
                    final_result_parts.append(f"**Web搜索结果:**\n{web_search_result}")
                    logger.info("已添加Web搜索结果到最终输出")
                
                final_result = "\n\n".join(final_result_parts) if final_result_parts else "未找到相关信息"
                logger.info(f"最终整合结果长度: {len(final_result)} 字符")
                
                return {
                    "background_investigation_results": final_result
                }
            else:
                logger.error(f"Tavily search returned malformed response: {searched_content}")
                return {"background_investigation_results": "搜索结果格式异常"}
        else:
            # 对于其他搜索引擎，暂时使用原始方法
            web_search_results = get_web_search_tool(
                configurable.max_search_results
            ).invoke(query)
            
            web_search_result = json.dumps(web_search_results, ensure_ascii=False)
            
            # 整合数据库查询结果和Web搜索结果
            final_result_parts = []
            if database_results and database_results.strip():
                final_result_parts.append(f"**数据库查询结果:**\n{database_results}")
                logger.info("已添加数据库查询结果到最终输出")
            
            if web_search_result and web_search_result.strip():
                final_result_parts.append(f"**Web搜索结果:**\n{web_search_result}")
                logger.info("已添加Web搜索结果到最终输出")
            
            final_result = "\n\n".join(final_result_parts) if final_result_parts else "未找到相关信息"
            logger.info(f"最终整合结果长度: {len(final_result)} 字符")
            
            return {
                "background_investigation_results": final_result
            }
    
    except Exception as e:
        logger.error(f"Enhanced background investigation failed: {str(e)}", exc_info=True)
        # 降级到原始方法
        logger.info("降级到原始背景调查方法")
        return background_investigation_node(state, config)


def planner_node_with_dependencies(
    state: State, config: RunnableConfig
) -> Command[Literal["human_feedback", "reporter"]]:
    """Enhanced planner node that uses dependency-aware prompt template.
    
    This version uses 'planner_with_dependencies' template that includes
    step dependency instructions for optimized token usage.
    """
    logger.info("Planner generating full plan (with dependency awareness)")
    configurable = Configuration.from_runnable_config(config)
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    
    # Use a different prompt template for dependency-aware planning
    messages = apply_prompt_template("planner_with_dependencies", state, configurable)

    if state.get("enable_background_investigation") and state.get(
        "background_investigation_results"
    ):
        messages += [
            {
                "role": "user",
                "content": (
                    "background investigation results of user query:\n"
                    + state["background_investigation_results"]
                    + "\n"
                ),
            }
        ]

    if configurable.enable_deep_thinking:
        llm = get_llm_by_type("reasoning")
    elif AGENT_LLM_MAP["planner"] == "basic":
        llm = get_llm_by_type("basic").with_structured_output(
            Plan,
            method="json_mode",
        )
    else:
        llm = get_llm_by_type(AGENT_LLM_MAP["planner"])

    # if the plan iterations is greater than the max plan iterations, return the reporter node
    if plan_iterations >= configurable.max_plan_iterations:
        return Command(goto="reporter")

    full_response = ""
    if AGENT_LLM_MAP["planner"] == "basic" and not configurable.enable_deep_thinking:
        response = llm.invoke(messages)
        full_response = response.model_dump_json(indent=4, exclude_none=True)
    else:
        response = llm.stream(messages)
        for chunk in response:
            full_response += chunk.content
    logger.debug(f"Current state messages: {state['messages']}")
    logger.info(f"Planner response: {full_response}")

    try:
        curr_plan = json.loads(repair_json_output(full_response))
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        if plan_iterations > 0:
            return Command(goto="reporter")
        else:
            return Command(goto="__end__")
    
    # Validate step dependencies if present
    if isinstance(curr_plan, dict) and "steps" in curr_plan:
        temp_plan = Plan.model_validate(curr_plan)
        errors = validate_step_dependencies(temp_plan)
        if errors:
            logger.warning(f"Dependency validation errors: {errors}")
            # Log visualization for debugging
            logger.debug(visualize_dependencies(temp_plan))
    
    if isinstance(curr_plan, dict) and curr_plan.get("has_enough_context"):
        logger.info("Planner response has enough context.")
        new_plan = Plan.model_validate(curr_plan)
        return Command(
            update={
                "messages": [AIMessage(content=full_response, name="planner")],
                "current_plan": new_plan,
            },
            goto="reporter",
        )
    return Command(
        update={
            "messages": [AIMessage(content=full_response, name="planner")],
            "current_plan": full_response,
        },
        goto="human_feedback",
    )


def build_context_for_step(current_step_index: int, completed_steps: list, plan: Plan, current_step) -> str:
    """Build context for a step based on its dependencies.
    
    This function implements the step dependency optimization to reduce token usage.
    Instead of blindly including all previous steps, it only includes the specific
    information needed based on the step's declared dependencies.
    
    Args:
        current_step_index: Index of the current step (0-based)
        completed_steps: List of already completed steps
        plan: The complete plan object
        current_step: The current step to execute
    
    Returns:
        Formatted context string for the agent
    """
    # Get the step definition with dependency info
    current_step_def = plan.steps[current_step_index]
    
    # Handle case where step has no dependencies or dependency_type is "none"
    if not hasattr(current_step_def, 'depends_on') or not current_step_def.depends_on or \
       (hasattr(current_step_def, 'dependency_type') and current_step_def.dependency_type == "none"):
        logger.info(f"Step {current_step_index} has no dependencies, using only current task")
        return f"# Current Step\n\n## Title\n{current_step.title}\n\n## Description\n{current_step.description}"
    
    # Build context from dependencies
    context = "# Relevant Previous Findings\n\n"
    
    for dep_index in current_step_def.depends_on:
        if dep_index >= len(completed_steps):
            logger.warning(f"Dependency index {dep_index} out of range for step {current_step_index}, skipping")
            continue
            
        dep_step = completed_steps[dep_index]
        dependency_type = getattr(current_step_def, 'dependency_type', 'full')  # Default to full for backward compatibility
        
        # Check if the dependency step was successful
        dep_status = getattr(dep_step, 'execution_status', ExecutionStatus.COMPLETED)
        if dep_status != ExecutionStatus.COMPLETED:
            logger.warning(f"Dependency step {dep_index} has status '{dep_status.value}', including limited info")
            context += f"## Completed Step {dep_index + 1}: {dep_step.title} (Status: {dep_status.value})\n"
            if dep_step.execution_res:
                context += f"<finding>\n{dep_step.execution_res}\n</finding>\n\n"
            else:
                context += "No results available due to execution failure.\n\n"
            continue
        
        logger.info(f"Including dependency from step {dep_index} with type '{dependency_type}'")
        
        if dependency_type == "summary":
            # Generate or use a summary of the step results
            summary = generate_step_summary(dep_step.execution_res)
            context += f"## Completed Step {dep_index + 1}: {dep_step.title}\n{summary}\n\n"
            
        elif dependency_type == "key_points":
            # Extract specific required information
            required_info = getattr(current_step_def, 'required_info', [])
            key_info = extract_required_info(dep_step.execution_res, required_info)
            context += f"## Completed Step {dep_index + 1}: {dep_step.title}\n{key_info}\n\n"
            
        elif dependency_type == "full":
            # Include complete results (use sparingly)
            context += f"## Completed Step {dep_index + 1}: {dep_step.title}\n"
            context += f"<finding>\n{dep_step.execution_res}\n</finding>\n\n"
        else:
            # Default to full if unknown type
            logger.warning(f"Unknown dependency type '{dependency_type}', defaulting to full")
            context += f"## Completed Step {dep_index + 1}: {dep_step.title}\n"
            context += f"<finding>\n{dep_step.execution_res}\n</finding>\n\n"
    
    # Add current task
    context += f"# Current Step\n\n## Title\n{current_step.title}\n\n## Description\n{current_step.description}"
    
    return context


def generate_step_summary(execution_result: str, max_length: int = 500) -> str:
    """Generate a summary of step execution results.
    
    Args:
        execution_result: The full execution result text
        max_length: Maximum length of the summary
        
    Returns:
        Summarized text
    """
    if not execution_result:
        return "No results available"
        
    if len(execution_result) <= max_length:
        return execution_result
    
    # Simple truncation for now - can be enhanced with LLM summarization later
    # Extract the first paragraph and any bullet points
    lines = execution_result.split('\n')
    summary_lines = []
    char_count = 0
    
    for line in lines:
        # Prioritize lines that look like headers or bullet points
        if line.strip().startswith(('##', '*', '-', '•', '1.', '2.', '3.')):
            if char_count + len(line) < max_length:
                summary_lines.append(line)
                char_count += len(line)
        elif char_count < max_length // 2:  # Include some regular text too
            summary_lines.append(line)
            char_count += len(line)
            
        if char_count >= max_length:
            break
    
    summary = '\n'.join(summary_lines)
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."
        
    return summary


def extract_required_info(execution_result: str, required_info: list) -> str:
    """Extract specific required information from execution results.
    
    Args:
        execution_result: The full execution result text
        required_info: List of required information types
        
    Returns:
        Extracted information formatted as text
    """
    if not required_info:
        return "No specific information requested"
        
    extracted = []
    
    for info_type in required_info:
        # Convert info_type to searchable terms
        search_terms = info_type.lower().replace('_', ' ').split()
        
        # Find relevant lines
        relevant_lines = []
        lines = execution_result.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Check if any search term appears in the line
            if any(term in line_lower for term in search_terms):
                relevant_lines.append(line.strip())
                # Also include the next line if it seems related
                if i + 1 < len(lines) and lines[i + 1].strip():
                    relevant_lines.append(lines[i + 1].strip())
        
        if relevant_lines:
            # Limit to first 3 most relevant lines
            relevant_text = '\n'.join(relevant_lines[:3])
            extracted.append(f"### {info_type}\n{relevant_text}")
        else:
            extracted.append(f"### {info_type}\nNo specific data found")
    
    return '\n\n'.join(extracted) if extracted else "No matching information found for requested data points"


async def _execute_agent_step_with_dependencies(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """Enhanced version of _execute_agent_step that uses dependency-based context building.
    
    This function replaces the original token-heavy approach with a smart context building
    mechanism that only includes relevant information based on step dependencies.
    """
    current_plan = state.get("current_plan")
    plan_title = current_plan.title
    observations = state.get("observations", [])

    # Find the first unexecuted step
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        # Check if step is pending (not yet executed)
        step_status = getattr(step, 'execution_status', ExecutionStatus.PENDING)
        if step_status == ExecutionStatus.PENDING and not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.warning("No unexecuted step found")
        return Command(goto="research_team")

    logger.info(f"Executing step: {current_step.title}, agent: {agent_name}")

    # Build context based on step dependencies instead of including all previous steps
    current_step_index = len(completed_steps)  # Current step is the next one to execute
    context_content = build_context_for_step(current_step_index, completed_steps, current_plan, current_step)
    
    # Log context size for monitoring
    logger.info(f"Context size for step {current_step_index}: {len(context_content)} characters")
    
    # Prepare the input for the agent with dependency-based context
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"# Research Topic\n\n{plan_title}\n\n{context_content}\n\n## Locale\n\n{state.get('locale', 'en-US')}"
            )
        ]
    }

    # Add citation reminder for researcher agent
    if agent_name == "researcher":
        if state.get("resources"):
            resources_info = "**The user mentioned the following resource files:**\n\n"
            for resource in state.get("resources"):
                resources_info += f"- {resource.title} ({resource.description})\n"

            agent_input["messages"].append(
                HumanMessage(
                    content=resources_info
                    + "\n\n"
                    + "You MUST use the **local_search_tool** to retrieve the information from the resource files.",
                )
            )

        agent_input["messages"].append(
            HumanMessage(
                content="IMPORTANT: DO NOT include inline citations in the text. Instead, track all sources and include a References section at the end using link reference format. Include an empty line between each citation for better readability. Use this format for each reference:\n- [Source Title](URL)\n\n- [Another Source](URL)",
                name="system",
            )
        )

    # Invoke the agent
    default_recursion_limit = 25
    try:
        env_value_str = os.getenv("AGENT_RECURSION_LIMIT", str(default_recursion_limit))
        parsed_limit = int(env_value_str)

        if parsed_limit > 0:
            recursion_limit = parsed_limit
            logger.info(f"Recursion limit set to: {recursion_limit}")
        else:
            logger.warning(
                f"AGENT_RECURSION_LIMIT value '{env_value_str}' (parsed as {parsed_limit}) is not positive. "
                f"Using default value {default_recursion_limit}."
            )
            recursion_limit = default_recursion_limit
    except ValueError:
        raw_env_value = os.getenv("AGENT_RECURSION_LIMIT")
        logger.warning(
            f"Invalid AGENT_RECURSION_LIMIT value: '{raw_env_value}'. "
            f"Using default value {default_recursion_limit}."
        )
        recursion_limit = default_recursion_limit

    logger.info(f"Agent input: {agent_input}")
    
    try:
        result = await agent.ainvoke(
            input=agent_input, config={"recursion_limit": recursion_limit}
        )

        # Process the result
        response_content = result["messages"][-1].content
        logger.debug(f"{agent_name.capitalize()} full response: {response_content}")

        # Update the step with the execution result
        current_step.execution_res = response_content
        current_step.execution_status = ExecutionStatus.COMPLETED
        logger.info(f"Step '{current_step.title}' execution completed by {agent_name}")
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Agent execution failed for step '{current_step.title}': {error_message}")
        
        # Handle specific API errors and set appropriate status
        if "Content Exists Risk" in error_message:
            logger.warning(f"⚠️  Content Exists Risk detected for step '{current_step.title}' - skipping due to content safety restrictions")
            current_step.execution_status = ExecutionStatus.SKIPPED
            current_step.error_message = f"Content Exists Risk: {error_message}"
            current_step.execution_res = "Step skipped due to content safety restrictions."
        elif "400" in error_message or "BadRequestError" in error_message:
            logger.warning(f"⚠️  API Bad Request for step '{current_step.title}' - marking as failed")
            current_step.execution_status = ExecutionStatus.FAILED
            current_step.error_message = f"API Error: {error_message}"
            current_step.execution_res = "Step failed due to API error."
        elif "429" in error_message or "rate_limit" in error_message.lower():
            logger.warning(f"⚠️  Rate limit reached for step '{current_step.title}' - marking as failed")
            current_step.execution_status = ExecutionStatus.RATE_LIMITED
            current_step.error_message = f"Rate Limit: {error_message}"
            current_step.execution_res = "Step failed due to API rate limit."
        else:
            logger.warning(f"⚠️  Unexpected error for step '{current_step.title}' - marking as failed")
            current_step.execution_status = ExecutionStatus.FAILED
            current_step.error_message = f"Unexpected Error: {error_message}"
            current_step.execution_res = "Step failed due to unexpected error."
        
        logger.info(f"Step '{current_step.title}' marked as {current_step.execution_status.value}, continuing to next step")

    # Determine the content to include in messages based on execution result
    message_content = current_step.execution_res if current_step.execution_res else "Step execution failed"
    
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=message_content,
                    name=agent_name,
                )
            ],
            "observations": observations + [message_content],
        },
        goto="research_team",
    )


async def _setup_and_execute_agent_step_with_dependencies(
    state: State,
    config: RunnableConfig,
    agent_type: str,
    default_tools: list,
) -> Command[Literal["research_team"]]:
    """Enhanced version of _setup_and_execute_agent_step that uses dependency-based execution.
    
    This function is identical to the original but calls _execute_agent_step_with_dependencies
    instead of _execute_agent_step to implement the token optimization.
    """
    configurable = Configuration.from_runnable_config(config)
    mcp_servers = {}
    enabled_tools = {}

    # Extract MCP server configuration for this agent type
    if configurable.mcp_settings:
        for server_name, server_config in configurable.mcp_settings["servers"].items():
            if (
                server_config["enabled_tools"]
                and agent_type in server_config["add_to_agents"]
            ):
                mcp_servers[server_name] = {
                    k: v
                    for k, v in server_config.items()
                    if k in ("transport", "command", "args", "url", "env")
                }
                for tool_name in server_config["enabled_tools"]:
                    enabled_tools[tool_name] = server_name

    # Create and execute agent with MCP tools if available
    if mcp_servers:
        async with MultiServerMCPClient(mcp_servers) as client:
            loaded_tools = default_tools[:]
            for tool in client.get_tools():
                if tool.name in enabled_tools:
                    tool.description = (
                        f"Powered by '{enabled_tools[tool.name]}'.\n{tool.description}"
                    )
                    loaded_tools.append(tool)
            agent = create_agent(agent_type, agent_type, loaded_tools, agent_type)
            return await _execute_agent_step_with_dependencies(state, agent, agent_type)
    else:
        # Use default tools if no MCP servers are configured
        agent = create_agent(agent_type, agent_type, default_tools, agent_type)
        return await _execute_agent_step_with_dependencies(state, agent, agent_type)


async def researcher_node_with_dependencies(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Enhanced researcher node that uses dependency-based context building.
    
    This version replaces the original researcher_node to implement token optimization
    by only including relevant previous step results based on declared dependencies.
    """
    logger.info("Researcher node is researching (with dependency optimization).")
    configurable = Configuration.from_runnable_config(config)
    tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
    retriever_tool = get_retriever_tool(state.get("resources", []))
    if retriever_tool:
        tools.insert(0, retriever_tool)
    logger.info(f"Researcher tools: {tools}")
    return await _setup_and_execute_agent_step_with_dependencies(
        state,
        config,
        "researcher",
        tools,
    )


async def coder_node_with_dependencies(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Enhanced coder node that uses dependency-based context building.
    
    This version replaces the original coder_node to implement token optimization
    by only including relevant previous step results based on declared dependencies.
    """
    logger.info("Coder node is coding (with dependency optimization).")
    return await _setup_and_execute_agent_step_with_dependencies(
        state,
        config,
        "coder",
        [python_repl_tool],
    )


def validate_step_dependencies(plan: Plan) -> list:
    """Validate step dependencies for correctness.
    
    Args:
        plan: The plan containing steps with dependencies
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    for i, step in enumerate(plan.steps):
        # Skip validation if step doesn't have dependency fields
        if not hasattr(step, 'depends_on'):
            continue
            
        # Check for invalid dependency indices
        for dep_index in step.depends_on:
            if dep_index >= i:
                errors.append(
                    f"Step {i} '{step.title}' cannot depend on step {dep_index} "
                    f"(circular or forward dependency)"
                )
            if dep_index < 0 or dep_index >= len(plan.steps):
                errors.append(
                    f"Step {i} '{step.title}' has invalid dependency index {dep_index}"
                )
        
        # Check that required_info is provided when using key_points
        if hasattr(step, 'dependency_type') and step.dependency_type == "key_points":
            if not hasattr(step, 'required_info') or not step.required_info:
                errors.append(
                    f"Step {i} '{step.title}' uses 'key_points' dependency "
                    f"but has no required_info specified"
                )
                
        # Check for self-dependency
        if i in step.depends_on:
            errors.append(f"Step {i} '{step.title}' cannot depend on itself")
    
    return errors


def visualize_dependencies(plan: Plan) -> str:
    """Generate a visual representation of step dependencies.
    
    Args:
        plan: The plan containing steps with dependencies
        
    Returns:
        ASCII visualization of the dependency graph
    """
    visualization = "# Step Dependency Visualization\n\n"
    
    for i, step in enumerate(plan.steps):
        visualization += f"**Step {i}**: {step.title}\n"
        visualization += f"  Type: {step.step_type}\n"
        
        # Handle cases where dependency fields might not exist
        if hasattr(step, 'depends_on') and step.depends_on:
            dep_type = getattr(step, 'dependency_type', 'unknown')
            visualization += f"  Dependencies: {step.depends_on} (type: {dep_type})\n"
            
            if dep_type == "key_points" and hasattr(step, 'required_info'):
                visualization += f"  Required info: {', '.join(step.required_info)}\n"
                
            # Show what this step depends on
            for dep_idx in step.depends_on:
                if 0 <= dep_idx < len(plan.steps):
                    visualization += f"    ← Depends on Step {dep_idx}: {plan.steps[dep_idx].title}\n"
        else:
            visualization += "  Dependencies: None (independent)\n"
        
        visualization += "\n"
    
    # Add dependency summary
    visualization += "## Dependency Summary\n\n"
    
    # Count dependency types
    dep_counts = {"none": 0, "summary": 0, "key_points": 0, "full": 0}
    for step in plan.steps:
        if hasattr(step, 'dependency_type'):
            dep_type = step.dependency_type
        elif not hasattr(step, 'depends_on') or not step.depends_on:
            dep_type = "none"
        else:
            dep_type = "unknown"
            
        if dep_type in dep_counts:
            dep_counts[dep_type] += 1
    
    visualization += f"- Independent steps (none): {dep_counts['none']}\n"
    visualization += f"- Summary dependencies: {dep_counts['summary']}\n"
    visualization += f"- Key points dependencies: {dep_counts['key_points']}\n"
    visualization += f"- Full dependencies: {dep_counts['full']}\n"
    
    return visualization


async def researcher_node_with_database(state: State, config: RunnableConfig) -> Command[Literal["research_team"]]:
    """增强版研究员节点 - 集成MindsDB数据库查询功能"""
    logger.info("Enhanced researcher node with Database integration is running.")
    
    configurable = Configuration.from_runnable_config(config)
    current_step = state["current_step"]
    
    # 初始化MindsDB工具
    mindsdb_tool = MindsDBMCPTool()
    mindsdb_config = MindsDBMCPConfig.load_from_file()
    
    # 构建工具列表（包括标准工具和数据库工具）
    tools = []
    
    # 添加标准搜索工具
    tools.append(get_web_search_tool(configurable.max_search_results))
    
    # 定义数据库查询工具函数
    async def database_query_tool_func(query: str, database: str = None) -> str:
        """Query database using MindsDB.
        
        Args:
            query: SQL query to execute
            database: Database name (defaults to htinfo_db)
            
        Returns:
            Query results as formatted string
        """
        if not database:
            database = mindsdb_config.get_default_database() or "htinfo_db"
        
        try:
            result = await mindsdb_tool.query_database(database, query)
            if result.get("success"):
                formatted_result = f"Database Query Results from {database}:\n"
                formatted_result += f"Query: {query}\n"
                formatted_result += f"Columns: {', '.join(result.get('columns', []))}\n"
                formatted_result += f"Records found: {len(result.get('data', []))}\n\n"
                
                for i, row in enumerate(result.get('data', [])[:10]):  # 限制显示前10条
                    formatted_result += f"Record {i+1}: {row}\n"
                    
                return formatted_result
            else:
                return f"Database query failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Database query error: {str(e)}"
    
    async def table_info_tool_func(database: str = None, table_name: str = None) -> str:
        """Get table structure information.
        
        Args:
            database: Database name (defaults to htinfo_db)
            table_name: Specific table name (optional)
            
        Returns:
            Table information as formatted string
        """
        if not database:
            database = mindsdb_config.get_default_database() or "htinfo_db"
            
        try:
            result = await mindsdb_tool.get_table_info(database, table_name)
            if result.get("success"):
                if table_name:
                    return f"Table structure for {database}.{table_name}:\n{result.get('data', [])}"
                else:
                    tables = [row[0] for row in result.get('data', [])]
                    return f"Available tables in {database}: {', '.join(tables)}"
            else:
                return f"Failed to get table info: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Table info error: {str(e)}"
    
    # 添加其他工具
    tools.extend([
        crawl_tool,
        get_retriever_tool(),
        python_repl_tool,
    ])
    
    # 创建代理
    agent = create_agent(
        "researcher",
        tools,
        configurable.llm_config,
    )
    
    # 获取数据库信息用于增强提示词
    database_info = ""
    try:
        available_databases = mindsdb_tool.get_available_databases()
        if available_databases:
            database_info = f"Available databases: {', '.join(available_databases)}"
            for db_name in available_databases:
                table_info = await mindsdb_tool.get_table_info(db_name)
                if table_info.get("success"):
                    tables = [row[0] for row in table_info.get("data", [])]
                    database_info += f"\n- {db_name}: {', '.join(tables)}"
    except Exception as e:
        logger.warning(f"Failed to get database info: {str(e)}")
        database_info = "Database information unavailable"
    
    # 构建增强的提示词，包含数据库信息
    enhanced_prompt = f"""
{current_step.description}

You have access to the following databases through MindsDB:
{database_info}

Available database functions (use these as tools in your research):
- For SQL queries: Use web search or python REPL to simulate: database_query_tool(query, database)
- For table info: Use web search to simulate: table_info_tool(database, table_name)

Research Strategy:
1. First check if the research topic relates to data that might be in the local databases
2. If relevant, try to query the databases for accurate, up-to-date information
3. Use web search for external information and context
4. Combine database insights with web research for comprehensive analysis

Current task: {current_step.description}
"""
    
    # 执行代理
    result = agent.invoke({
        "messages": [
            HumanMessage(content=enhanced_prompt)
        ]
    })
    
    return Command(
        update={
            "messages": [result["messages"][-1]],
            "current_step": current_step
        },
        goto="research_team"
    )