# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import json
import logging
import os
from typing import Annotated, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.agents import create_agent
from src.tools.search import LoggedTavilySearch
from src.tools import (
    crawl_tool,
    get_web_search_tool,
    get_retriever_tool,
    python_repl_tool,
)

from src.config.agents import AGENT_LLM_MAP
from src.config.configuration import Configuration
from src.llms.llm import get_llm_by_type
from src.prompts.planner_model import Plan
from src.prompts.template import apply_prompt_template
from src.utils.json_utils import repair_json_output
from src.utils.token_manager import TokenManager

from .types import State
from ..config import SELECTED_SEARCH_ENGINE, SearchEngine

logger = logging.getLogger(__name__)


@tool
def handoff_to_planner(
    research_topic: Annotated[str, "The topic of the research task to be handed off."],
    locale: Annotated[str, "The user's detected language locale (e.g., en-US, zh-CN)."],
):
    """Handoff to planner agent to do plan."""
    # This tool is not returning anything: we're just using it
    # as a way for LLM to signal that it needs to hand off to planner agent
    return


def background_investigation_node(state: State, config: RunnableConfig):
    logger.info("background investigation node is running.")
    configurable = Configuration.from_runnable_config(config)
    query = state.get("research_topic")
    background_investigation_results = None
    
    # Initialize token manager for result trimming
    token_manager = TokenManager()
    
    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        searched_content = LoggedTavilySearch(
            max_results=configurable.max_search_results
        ).invoke(query)
        if isinstance(searched_content, list):
            background_investigation_results = [
                f"## {elem['title']}\n\n{elem['content']}" for elem in searched_content
            ]
            
            # Apply length management to background investigation results
            combined_results = "\n\n".join(background_investigation_results)
            
            # Trim if too long based on background_investigation strategy
            strategy = token_manager.get_trimming_strategy("background_investigation")
            max_length = strategy.get("max_tokens", 2000) * 4  # Rough token-to-char conversion
            
            if len(combined_results) > max_length:
                # Keep the most recent results
                trimmed_results = combined_results[:max_length] + "\n\n[... results truncated for token management ...]"
                from src.utils.token_counter import count_tokens
                from src.config import load_yaml_config
                
                # 获取当前使用的模型
                config_data = load_yaml_config("conf.yaml")
                current_model = config_data.get("BASIC_MODEL", {}).get("model", "deepseek-chat")
                
                original_tokens = count_tokens(combined_results, current_model)
                trimmed_tokens = count_tokens(trimmed_results, current_model)
                logger.info(
                    f"Background Investigation Trimming: "
                    f"Characters: {len(combined_results):,} → {len(trimmed_results):,} | "
                    f"Tokens (approx): {original_tokens:,} → {trimmed_tokens:,} | "
                    f"Reduction: {((len(combined_results) - len(trimmed_results)) / len(combined_results) * 100):.1f}%"
                )
                combined_results = trimmed_results
            
            return {
                "background_investigation_results": combined_results
            }
        else:
            logger.error(
                f"Tavily search returned malformed response: {searched_content}"
            )
    else:
        background_investigation_results = get_web_search_tool(
            configurable.max_search_results
        ).invoke(query)
        
        # Apply length management for non-Tavily results
        results_str = json.dumps(background_investigation_results, ensure_ascii=False)
        strategy = token_manager.get_trimming_strategy("background_investigation")
        max_length = strategy.get("max_tokens", 2000) * 4  # Rough token-to-char conversion
        
        if len(results_str) > max_length:
            results_str = results_str[:max_length] + "\n... [results truncated for token management]"
            logger.info(f"Background investigation JSON results trimmed to {len(results_str)} characters")
    
    return {
        "background_investigation_results": results_str if 'results_str' in locals() else json.dumps(
            background_investigation_results, ensure_ascii=False
        )
    }


def planner_node(
    state: State, config: RunnableConfig
) -> Command[Literal["human_feedback", "reporter"]]:
    """Planner node that generate the full plan."""
    logger.info("Planner generating full plan")
    configurable = Configuration.from_runnable_config(config)
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    messages = apply_prompt_template("planner", state, configurable)

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

    # Initialize token manager and get model name for trimming
    token_manager = TokenManager()
    from src.config import load_yaml_config
    config_data = load_yaml_config(token_manager.config_path)
    current_model = config_data.get("BASIC_MODEL", {}).get("model", "default")
    
    # Convert messages to BaseMessage objects for trimming
    base_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            # Handle dictionary format
            if msg["role"] == "system":
                from langchain_core.messages import SystemMessage
                base_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                base_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                base_messages.append(AIMessage(content=msg["content"]))
        else:
            # Handle BaseMessage objects directly
            base_messages.append(msg)
    
    # Trim messages for planner node
    trimmed_messages = token_manager.trim_messages_for_node(
        base_messages, current_model, "planner"
    )
    
    # Convert back to dict format for LLM
    messages = []
    for msg in trimmed_messages:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})
        elif hasattr(msg, 'content'):
            # Handle SystemMessage and other message types
            messages.append({"role": "system", "content": msg.content})
    
    # Token management logging is handled automatically in trim_messages_for_node

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
    if curr_plan.get("has_enough_context"):
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


def human_feedback_node(
    state,
) -> Command[Literal["planner", "research_team", "reporter", "__end__"]]:
    current_plan = state.get("current_plan", "")
    # check if the plan is auto accepted
    auto_accepted_plan = state.get("auto_accepted_plan", False)
    if not auto_accepted_plan:
        feedback = interrupt("Please Review the Plan.")

        # if the feedback is not accepted, return the planner node
        if feedback and str(feedback).upper().startswith("[EDIT_PLAN]"):
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=feedback, name="feedback"),
                    ],
                },
                goto="planner",
            )
        elif feedback and str(feedback).upper().startswith("[ACCEPTED]"):
            logger.info("Plan is accepted by user.")
        else:
            raise TypeError(f"Interrupt value of {feedback} is not supported.")

    # if the plan is accepted, run the following node
    plan_iterations = state["plan_iterations"] if state.get("plan_iterations", 0) else 0
    goto = "research_team"
    try:
        current_plan = repair_json_output(current_plan)
        # increment the plan iterations
        plan_iterations += 1
        # parse the plan
        new_plan = json.loads(current_plan)
        if new_plan["has_enough_context"]:
            goto = "reporter"
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        if plan_iterations > 1:  # the plan_iterations is increased before this check
            return Command(goto="reporter")
        else:
            return Command(goto="__end__")

    return Command(
        update={
            "current_plan": Plan.model_validate(new_plan),
            "plan_iterations": plan_iterations,
            "locale": new_plan["locale"],
        },
        goto=goto,
    )


def coordinator_node(
    state: State, config: RunnableConfig
) -> Command[Literal["planner", "background_investigator", "__end__"]]:
    """Coordinator node that communicate with customers."""
    logger.info("Coordinator talking.")
    configurable = Configuration.from_runnable_config(config)
    messages = apply_prompt_template("coordinator", state)
    response = (
        get_llm_by_type(AGENT_LLM_MAP["coordinator"])
        .bind_tools([handoff_to_planner])
        .invoke(messages)
    )
    logger.debug(f"Current state messages: {state['messages']}")

    goto = "__end__"
    locale = state.get("locale", "en-US")  # Default locale if not specified
    research_topic = state.get("research_topic", "")

    if len(response.tool_calls) > 0:
        goto = "planner"
        if state.get("enable_background_investigation"):
            # if the search_before_planning is True, add the web search tool to the planner agent
            goto = "background_investigator"
        try:
            for tool_call in response.tool_calls:
                if tool_call.get("name", "") != "handoff_to_planner":
                    continue
                if tool_call.get("args", {}).get("locale") and tool_call.get(
                    "args", {}
                ).get("research_topic"):
                    locale = tool_call.get("args", {}).get("locale")
                    research_topic = tool_call.get("args", {}).get("research_topic")
                    break
        except Exception as e:
            logger.error(f"Error processing tool calls: {e}")
    else:
        logger.warning(
            "Coordinator response contains no tool calls. Terminating workflow execution."
        )
        logger.debug(f"Coordinator response: {response}")

    return Command(
        update={
            "locale": locale,
            "research_topic": research_topic,
            "resources": configurable.resources,
        },
        goto=goto,
    )


def reporter_node(state: State, config: RunnableConfig):
    """Reporter node that write a final report."""
    logger.info("Reporter write final report")
    configurable = Configuration.from_runnable_config(config)
    current_plan = state.get("current_plan")
    input_ = {
        "messages": [
            HumanMessage(
                f"# Research Requirements\n\n## Task\n\n{current_plan.title}\n\n## Description\n\n{current_plan.thought}"
            )
        ],
        "locale": state.get("locale", "en-US"),
    }
    invoke_messages = apply_prompt_template("reporter", input_, configurable)
    observations = state.get("observations", [])

    # Initialize token manager for observation management
    token_manager = TokenManager()
    from src.config import load_yaml_config
    config_data = load_yaml_config(token_manager.config_path)
    current_model = config_data.get("BASIC_MODEL", {}).get("model", "default")
    
    # Manage observations to prevent token overflow
    managed_observations = token_manager.manage_observations(observations)
    
    # Log observation management if any changes were made
    if len(managed_observations) != len(observations):
        logger.info(f"Managed observations: {len(observations)} -> {len(managed_observations)}")

    # Add a reminder about the new report format, citation style, and table usage
    invoke_messages.append(
        HumanMessage(
            content="IMPORTANT: Structure your report according to the format in the prompt. Remember to include:\n\n1. Key Points - A bulleted list of the most important findings\n2. Overview - A brief introduction to the topic\n3. Detailed Analysis - Organized into logical sections\n4. Survey Note (optional) - For more comprehensive reports\n5. Key Citations - List all references at the end\n\nFor citations, DO NOT include inline citations in the text. Instead, place all citations in the 'Key Citations' section at the end using the format: `- [Source Title](URL)`. Include an empty line between each citation for better readability.\n\nPRIORITIZE USING MARKDOWN TABLES for data presentation and comparison. Use tables whenever presenting comparative data, statistics, features, or options. Structure tables with clear headers and aligned columns. Example table format:\n\n| Feature | Description | Pros | Cons |\n|---------|-------------|------|------|\n| Feature 1 | Description 1 | Pros 1 | Cons 1 |\n| Feature 2 | Description 2 | Pros 2 | Cons 2 |",
            name="system",
        )
    )

    # Add managed observations instead of all observations
    for observation in managed_observations:
        invoke_messages.append(
            HumanMessage(
                content=f"Below are some observations for the research task:\n\n{observation}",
                name="observation",
            )
        )
    
    # Apply token management to final invoke_messages
    trimmed_messages = token_manager.trim_messages_for_node(
        invoke_messages, current_model, "reporter"
    )
    
    # Log token management
    if len(trimmed_messages) < len(invoke_messages):
        token_manager.log_token_usage("reporter", len(invoke_messages), len(trimmed_messages))
    
    logger.debug(f"Current invoke messages: {trimmed_messages}")
    response = get_llm_by_type(AGENT_LLM_MAP["reporter"]).invoke(trimmed_messages)
    response_content = response.content
    logger.info(f"reporter response: {response_content}")

    return {"final_report": response_content}


def research_team_node(state: State):
    """Research team node that collaborates on tasks."""
    logger.info("Research team is collaborating on tasks.")
    pass


async def _execute_agent_step(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """Helper function to execute a step using the specified agent."""
    current_plan = state.get("current_plan")
    observations = state.get("observations", [])

    # Find the first unexecuted step
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        if not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.warning("No unexecuted step found")
        return Command(goto="research_team")

    logger.info(f"Executing step: {current_step.title}, agent: {agent_name}")

    # Format completed steps information
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# Existing Research Findings\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## Existing Finding {i + 1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # Prepare the input for the agent with completed steps info
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"{completed_steps_info}# Current Task\n\n## Title\n\n{current_step.title}\n\n## Description\n\n{current_step.description}\n\n## Locale\n\n{state.get('locale', 'en-US')}"
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

    # Apply token management for researcher agent
    # NOTE: Token management is now handled in agents.py pre_model_hook
    if False and agent_name == "researcher":
        from src.utils.token_manager import TokenManager
        from src.config import load_yaml_config
        from langchain_core.messages import BaseMessage, SystemMessage
        from src.utils.token_counter import TokenCounterFactory
        
        token_manager = TokenManager()
        config_data = load_yaml_config(token_manager.config_path)
        current_model = config_data.get("BASIC_MODEL", {}).get("model", "deepseek-chat")
        
        # Convert messages to BaseMessage format if needed
        messages = agent_input.get("messages", [])
        if messages and not isinstance(messages[0], BaseMessage):
            # Messages are already BaseMessage objects, no conversion needed
            pass
        
        # 🔍 DEBUG: 详细记录 token 管理前的状态
        try:
            counter = TokenCounterFactory.create_counter(current_model)
            # 转换为字典格式进行计数
            message_dicts = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    if isinstance(msg, SystemMessage):
                        message_dicts.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        message_dicts.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        message_dicts.append({"role": "assistant", "content": msg.content})
                    elif hasattr(msg, 'role'):
                        message_dicts.append({"role": msg.role, "content": msg.content})
            
            pre_trim_tokens = counter.count_messages_tokens(message_dicts)
            logger.info(f"🔍 PRE-TRIM DEBUG [{agent_name}]: {len(messages)} messages, {pre_trim_tokens:,} tokens")
            
            # 记录最大的几条消息
            if len(messages) > 5:
                for i, msg in enumerate(messages[-5:], len(messages)-5):
                    content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                    logger.info(f"  Message {i}: {type(msg).__name__} - {len(str(msg.content))} chars: {content_preview}")
        except Exception as e:
            logger.warning(f"🔍 PRE-TRIM DEBUG failed: {e}")
        
        # Trim messages for researcher node
        trimmed_messages = token_manager.trim_messages_for_node(
            messages, current_model, "researcher"
        )
        
        # 🔍 DEBUG: 详细记录 token 管理后的状态
        try:
            trimmed_dicts = []
            for msg in trimmed_messages:
                if hasattr(msg, 'content'):
                    if isinstance(msg, SystemMessage):
                        trimmed_dicts.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        trimmed_dicts.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        trimmed_dicts.append({"role": "assistant", "content": msg.content})
                    elif hasattr(msg, 'role'):
                        trimmed_dicts.append({"role": msg.role, "content": msg.content})
            
            post_trim_tokens = counter.count_messages_tokens(trimmed_dicts)
            logger.info(f"🔍 POST-TRIM DEBUG [{agent_name}]: {len(trimmed_messages)} messages, {post_trim_tokens:,} tokens")
            
            # 检查是否超过模型限制
            model_limit = token_manager.get_model_limit(current_model)
            if post_trim_tokens > model_limit:
                logger.error(f"🚨 STILL OVER LIMIT [{agent_name}]: {post_trim_tokens:,} > {model_limit:,} tokens!")
                # 记录前几条和后几条消息
                for i, msg in enumerate(trimmed_messages[:3]):
                    content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                    logger.error(f"  First {i}: {type(msg).__name__} - {len(str(msg.content))} chars: {content_preview}")
                for i, msg in enumerate(trimmed_messages[-3:], len(trimmed_messages)-3):
                    content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                    logger.error(f"  Last {i}: {type(msg).__name__} - {len(str(msg.content))} chars: {content_preview}")
        except Exception as e:
            logger.warning(f"🔍 POST-TRIM DEBUG failed: {e}")
        
        # Update agent input with trimmed messages
        agent_input["messages"] = trimmed_messages
        
        logger.info(f"Token management applied for {agent_name}: {len(messages)} → {len(trimmed_messages)} messages")
    
    logger.info(f"Agent input: {agent_input}")
    
    # 🔍 FINAL DEBUG & FIX: 在实际调用 LLM 前的最后检查和修复
    # NOTE: Final check disabled - token management now in agents.py pre_model_hook
    logger.debug(f"🔍 FINAL CHECK disabled for agent: {agent_name}")
    
    if False and agent_name == "researcher":
        logger.error(f"🔍 INSIDE researcher condition")
        try:
            final_messages = agent_input.get("messages", [])
            from src.utils.token_counter import TokenCounterFactory
            from src.config import load_yaml_config
            
            # 获取当前使用的模型
            config_data = load_yaml_config("conf.yaml")
            current_model = config_data.get("BASIC_MODEL", {}).get("model", "deepseek-chat")
            
            counter = TokenCounterFactory.create_counter(current_model)
            
            final_dicts = []
            for msg in final_messages:
                if hasattr(msg, 'content'):
                    if isinstance(msg, SystemMessage):
                        final_dicts.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        final_dicts.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        final_dicts.append({"role": "assistant", "content": msg.content})
                    elif hasattr(msg, 'role'):
                        final_dicts.append({"role": msg.role, "content": msg.content})
            
            final_tokens = counter.count_messages_tokens(final_dicts)
            logger.info(f"🔍 FINAL CHECK [{agent_name}]: {len(final_messages)} messages, {final_tokens:,} tokens")
            
            # 记录每条消息的详细信息
            for i, msg in enumerate(final_messages):
                content_preview = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)
                msg_tokens = counter.count_messages_tokens([final_dicts[i]] if i < len(final_dicts) else [])
                logger.debug(f"  Message[{i}] {type(msg).__name__}: {msg_tokens} tokens - {content_preview}")
            
            # 获取模型的实际限制
            from src.utils.token_manager import TokenManager
            token_manager = TokenManager()
            model_limit = token_manager.get_model_limit(current_model)
            
            if final_tokens > model_limit:
                logger.error(f"🚨 CRITICAL: About to send {final_tokens:,} tokens to LLM (limit: {model_limit:,})! Applying emergency token management!")
                
                # 应用激进的 Token 管理
                emergency_trimmed = token_manager.trim_messages_for_node(
                    final_messages, current_model, "researcher"
                )
                
                # 重新计算
                emergency_dicts = []
                for msg in emergency_trimmed:
                    if hasattr(msg, 'content'):
                        if isinstance(msg, SystemMessage):
                            emergency_dicts.append({"role": "system", "content": msg.content})
                        elif isinstance(msg, HumanMessage):
                            emergency_dicts.append({"role": "user", "content": msg.content})
                        elif isinstance(msg, AIMessage):
                            emergency_dicts.append({"role": "assistant", "content": msg.content})
                
                emergency_tokens = counter.count_messages_tokens(emergency_dicts)
                logger.error(f"🔧 EMERGENCY TRIM: {len(final_messages)} → {len(emergency_trimmed)} messages, {final_tokens:,} → {emergency_tokens:,} tokens (model: {current_model}, limit: {model_limit:,})")
                
                # 检查是否仍然超限
                if emergency_tokens > model_limit:
                    logger.error(f"⚠️ WARNING: Emergency trim still over limit by {emergency_tokens - model_limit:,} tokens!")
                else:
                    logger.info(f"✅ Emergency trim successful: {emergency_tokens:,} <= {model_limit:,} tokens")
                
                # 记录修剪后的消息详情
                for i, msg in enumerate(emergency_trimmed):
                    content_preview = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)
                    msg_tokens = counter.count_messages_tokens([emergency_dicts[i]] if i < len(emergency_dicts) else [])
                    logger.debug(f"  Trimmed[{i}] {type(msg).__name__}: {msg_tokens} tokens - {content_preview}")
                
                # 更新 agent_input
                agent_input["messages"] = emergency_trimmed
        except Exception as e:
            logger.warning(f"🔍 FINAL CHECK failed: {e}")
    
    logger.error(f"🔍 ABOUT TO CALL agent.ainvoke for {agent_name}")
    
    # 添加内容安全错误处理
    try:
        result = await agent.ainvoke(
            input=agent_input, config={"recursion_limit": recursion_limit}
        )
        logger.error(f"🔍 COMPLETED agent.ainvoke for {agent_name}")
    except Exception as e:
        # 导入内容安全处理器
        from src.utils.content_safety_handler import content_safety_handler, ContentSafetyError
        from openai import BadRequestError
        
        if isinstance(e, BadRequestError) and content_safety_handler.is_content_safety_error(e):
            logger.warning(f"🚨 {agent_name} 遇到内容安全检查错误: {e}")
            
            # 构建错误上下文
            context = {
                "agent_name": agent_name,
                "step_title": current_step.title if current_step else "Unknown",
                "message_count": len(agent_input.get("messages", [])),
                "error_time": "2025-07-10 10:37:21"  # 可以改为实时时间
            }
            
            # 处理内容安全错误
            action = await content_safety_handler.handle_content_safety_error(
                e, 
                context, 
                auto_continue_timeout=30  # 30秒后自动继续
            )
            
            if action == "continue":
                # 创建显眼的安全提示响应
                logger.info(f"🔄 {agent_name} 内容安全错误，自动过滤并继续")
                
                # 构建显眼的安全响应消息
                from langchain_core.messages import AIMessage
                safe_response = AIMessage(
                    content=f"⚠️ **内容安全提示** ⚠️\n\n"
                           f"🚫 **检测到内容风险**: 当前查询内容触发了API的安全检查机制\n\n"
                           f"🔧 **自动处理**: 系统已自动过滤风险内容并继续执行\n\n"
                           f"📋 **当前任务**: {current_step.title if current_step else '未知任务'}\n\n"
                           f"💡 **建议**: 如需更详细信息，请尝试:\n"
                           f"• 调整查询关键词，避免敏感词汇\n"
                           f"• 换个角度或更具体的方式描述问题\n"
                           f"• 将复杂问题分解为多个简单查询\n\n"
                           f"✅ **继续执行**: 系统将跳过此部分内容，继续执行后续研究步骤..."
                )
                
                result = {"messages": [safe_response]}
                
            # 由于现在只返回"continue"，这些分支保留用于向后兼容
            elif action == "stop":
                logger.error(f"🛑 {agent_name} 内容安全错误，停止任务")
                raise ContentSafetyError(f"{agent_name} 遇到内容安全限制，任务已停止", e)
            elif action == "retry":
                logger.warning(f"🔄 {agent_name} 内容安全错误，重试")
                raise e
            else:
                # 未知操作，抛出原错误
                raise e
        else:
            # 非内容安全错误，直接抛出
            logger.error(f"❌ {agent_name} 执行失败: {e}")
            raise e

    # Process the result
    response_content = result["messages"][-1].content
    logger.debug(f"{agent_name.capitalize()} full response: {response_content}")

    # 🎯 新增：Tool执行后的Token检查点
    # 检查response_content的长度，防止单个响应过大
    max_response_length = 15000  # 限制单个响应最大长度
    if len(str(response_content)) > max_response_length:
        original_length = len(str(response_content))
        # 截断响应，保留开头和结尾
        half_length = max_response_length // 2
        response_content = (
            str(response_content)[:half_length] + 
            f"\n\n[... 响应内容已截断，原长度: {original_length} 字符 ...]\n\n" +
            str(response_content)[-half_length:]
        )
        logger.warning(f"🔧 {agent_name}: Response truncated ({original_length} → {len(response_content)} chars)")

    # Update the step with the execution result
    current_step.execution_res = response_content
    logger.info(f"Step '{current_step.title}' execution completed by {agent_name}")

    # 🔍 DEBUG: 监控 Command 参数，查找异步回调错误的根因
    try:
        logger.debug(f"🔍 Command parameters debug:")
        logger.debug(f"  agent_name: {repr(agent_name)} (type: {type(agent_name)})")
        logger.debug(f"  response_content length: {len(str(response_content))} chars")
        logger.debug(f"  response_content type: {type(response_content)}")
        logger.debug(f"  response_content preview: {repr(str(response_content)[:200])}")
        logger.debug(f"  observations count: {len(observations)}")
        logger.debug(f"  observations types: {[type(obs) for obs in observations]}")
        
        # 检查 response_content 的有效性
        if response_content is None:
            logger.warning("⚠️ response_content is None!")
        elif not isinstance(response_content, (str, int, float, bool, list, dict)):
            logger.warning(f"⚠️ response_content has unusual type: {type(response_content)}")
        
        # 检查 observations 的有效性
        for i, obs in enumerate(observations):
            if obs is None:
                logger.warning(f"⚠️ observations[{i}] is None!")
            elif not isinstance(obs, (str, int, float, bool, list, dict)):
                logger.warning(f"⚠️ observations[{i}] has unusual type: {type(obs)}")
        
        # 创建 HumanMessage，检查是否有问题
        human_message = HumanMessage(
            content=response_content,
            name=agent_name,
        )
        logger.debug(f"  HumanMessage created successfully: {type(human_message)}")
        
        # 🎯 新增：Observations管理，防止累积过多
        updated_observations = observations + [response_content]
        max_observations = 5  # 最多保留5个观察结果
        
        if len(updated_observations) > max_observations:
            # 保留最近的观察结果
            managed_observations = updated_observations[-max_observations:]
            logger.info(f"🔧 {agent_name}: Observations trimmed ({len(updated_observations)} → {len(managed_observations)})")
        else:
            managed_observations = updated_observations
        
        # 创建 update 字典
        update_dict = {
            "messages": [human_message],
            "observations": managed_observations,
        }
        logger.debug(f"  update_dict created successfully, keys: {list(update_dict.keys())}")
        
    except Exception as debug_e:
        logger.error(f"🚨 DEBUG failed while preparing Command: {debug_e}")
        import traceback
        logger.error(f"Debug traceback: {traceback.format_exc()}")

    # 返回执行结果
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response_content,
                    name=agent_name,
                )
            ],
            "observations": observations + [response_content],
        },
        goto="research_team",
    )


async def _setup_and_execute_agent_step(
    state: State,
    config: RunnableConfig,
    agent_type: str,
    default_tools: list,
) -> Command[Literal["research_team"]]:
    """Helper function to set up an agent with appropriate tools and execute a step.

    This function handles the common logic for both researcher_node and coder_node:
    1. Configures MCP servers and tools based on agent type
    2. Creates an agent with the appropriate tools or uses the default agent
    3. Executes the agent on the current step

    Args:
        state: The current state
        config: The runnable config
        agent_type: The type of agent ("researcher" or "coder")
        default_tools: The default tools to add to the agent

    Returns:
        Command to update state and go to research_team
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
            return await _execute_agent_step(state, agent, agent_type)
    else:
        # Use default tools if no MCP servers are configured
        agent = create_agent(agent_type, agent_type, default_tools, agent_type)
        return await _execute_agent_step(state, agent, agent_type)


async def researcher_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Researcher node that do research"""
    logger.info("Researcher node is researching.")
    configurable = Configuration.from_runnable_config(config)
    tools = [get_web_search_tool(configurable.max_search_results), crawl_tool]
    retriever_tool = get_retriever_tool(state.get("resources", []))
    if retriever_tool:
        tools.insert(0, retriever_tool)
    logger.info(f"Researcher tools: {tools}")
    return await _setup_and_execute_agent_step(
        state,
        config,
        "researcher",
        tools,
    )


async def coder_node(
    state: State, config: RunnableConfig
) -> Command[Literal["research_team"]]:
    """Coder node that do code analysis."""
    logger.info("Coder node is coding.")
    return await _setup_and_execute_agent_step(
        state,
        config,
        "coder",
        [python_repl_tool],
    )
