"""
Refactored Database Nodes with improved code structure and English prompts
- Separated strategy guidance into external template files  
- Converted internal messages to English
- Maintained Chinese user-facing responses where appropriate
"""

import os
import logging
from typing import Dict, Any, Literal
from jinja2 import Template

from langgraph.types import Command
from langgraph.types import RunnableConfig as Configuration
from langchain_core.messages import HumanMessage, AIMessage

from src.prompts.template import apply_prompt_template
from src.llms.llm import get_llm_by_type
from src.config.agents import create_agent
from src.tools.mindsdb_mcp import mindsdb_query_tool, mindsdb_table_info_tool
from src.graph.types import State
from src.prompts.planner_model import QueryStrategy, ResultSize

logger = logging.getLogger(__name__)

def _get_strategy_guidance(step) -> str:
    """Generate execution guidance based on query strategy"""
    
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


def _analyze_execution_result(step, execution_result: str) -> Dict[str, Any]:
    """Analyze execution result efficiency"""
    analysis = {
        "is_efficient": True,
        "warnings": [],
        "suggestions": [],
        "data_volume_estimate": "unknown"
    }
    
    # Check for indicators of large data returns
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
        analysis["warnings"].append("Query returned large dataset")
        analysis["suggestions"].append("Consider using aggregation or sampling strategy")
        analysis["data_volume_estimate"] = "large"
    
    # Check for aggregated results (efficient patterns)
    aggregation_patterns = [
        "COUNT(*)",
        "SUM(",
        "AVG(",
        "MAX(",
        "MIN(",
        "GROUP BY",
        "aggregated"
    ]
    
    if any(pattern in execution_result for pattern in aggregation_patterns):
        analysis["data_volume_estimate"] = "aggregated"
        
    # Check for sampling patterns
    if "LIMIT" in execution_result:
        analysis["data_volume_estimate"] = "sampled"
    
    return analysis


async def database_researcher_node_refactored(
    state: State, config: Configuration
) -> Command[Literal["research_team"]]:
    """Refactored Database Researcher Node with improved prompts"""
    logger.info("Database researcher starting query analysis")
    
    try:
        configurable = Configuration.from_runnable_config(config)
        
        # Create MindsDB tools
        tools = [mindsdb_query_tool, mindsdb_table_info_tool]
        
        # Create database researcher agent
        database_researcher_agent = create_agent(
            agent_name="database_researcher",
            agent_type="researcher", 
            tools=tools,
            prompt_template="researcher"
        )
        
        logger.info(f"Database researcher tools: {tools}")
        
        return await _execute_database_agent_step_refactored(
            state,
            database_researcher_agent,
            "database_researcher"
        )
        
    except Exception as e:
        logger.error(f"Database researcher node failed: {str(e)}", exc_info=True)
        return Command(goto="research_team")


async def _execute_database_agent_step_refactored(
    state: State, agent, agent_name: str
) -> Command[Literal["research_team"]]:
    """Execute database analysis step with refactored guidance"""
    current_plan = state.get("current_plan")
    if not current_plan:
        logger.warning("Missing analysis plan, cannot execute step")
        return Command(goto="research_team")
    
    plan_title = current_plan.title
    
    # Find first unexecuted step
    current_step = None
    completed_steps = []
    for step in current_plan.steps:
        if not step.execution_res:
            current_step = step
            break
        else:
            completed_steps.append(step)

    if not current_step:
        logger.info("All steps completed, conditional routing will handle next step")
        return Command(goto="research_team")

    logger.info(f"Executing database analysis step: {current_step.title}, agent: {agent_name}")

    # Format completed steps information
    completed_steps_info = ""
    if completed_steps:
        completed_steps_info = "# Previously Completed Analysis Steps\n\n"
        for i, step in enumerate(completed_steps):
            completed_steps_info += f"## Completed Step {i + 1}: {step.title}\n\n"
            completed_steps_info += f"<finding>\n{step.execution_res}\n</finding>\n\n"

    # Get strategy guidance
    strategy_guidance = _get_strategy_guidance(current_step)
    
    # Prepare agent input with English prompts
    agent_input = {
        "messages": [
            HumanMessage(
                content=f"# Database Analysis Topic\n\n{plan_title}\n\n{completed_steps_info}# Current Step\n\n## Title\n\n{current_step.title}\n\n## Description\n\n{current_step.description}\n\n## Query Strategy Guidance\n\n{strategy_guidance}\n\n## Language Setting\n\n{state.get('locale', 'zh-CN')}"
            )
        ]
    }

    try:
        # Execute agent step
        result = await agent.ainvoke(agent_input)
        execution_result = result["messages"][-1].content

        # Analyze execution efficiency
        efficiency_analysis = _analyze_execution_result(current_step, execution_result)
        
        # Log efficiency analysis results
        if not efficiency_analysis["is_efficient"]:
            logger.warning(f"Step '{current_step.title}' efficiency warning: {efficiency_analysis['warnings']}")
            for suggestion in efficiency_analysis["suggestions"]:
                logger.info(f"Optimization suggestion: {suggestion}")
        
        logger.info(f"Step '{current_step.title}' data volume estimate: {efficiency_analysis['data_volume_estimate']}")

        # Update step execution result
        current_step.execution_res = execution_result

        # Update state
        return Command(
            update={
                "messages": [AIMessage(content=execution_result, name=agent_name)],
                "current_plan": current_plan,
            },
            goto="research_team"
        )

    except Exception as e:
        logger.error(f"Database agent step execution failed: {str(e)}", exc_info=True)
        error_msg = f"Database analysis step failed: {str(e)}"
        current_step.execution_res = error_msg
        
        return Command(
            update={
                "messages": [AIMessage(content=error_msg, name=agent_name)],
                "current_plan": current_plan,
            },
            goto="research_team"
        )