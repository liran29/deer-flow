# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.prompts.planner_model import StepType

from .types import State
from .nodes import (
    coordinator_node,
    planner_node,
    reporter_node,
    research_team_node,
    researcher_node,
    coder_node,
    human_feedback_node,
    background_investigation_node,
)

# Step dependency optimization nodes (imported from separate module)
from .nodes_enhanced import (
    background_investigation_node_enhanced,
    planner_node_with_dependencies,
    researcher_node_with_dependencies,
    coder_node_with_dependencies,
)

from src.utils.enhanced_features import (
    is_enhanced_background_investigation_enabled,
    is_step_dependency_optimization_enabled,
    has_enhanced_features_enabled,
)

def continue_to_running_research_team(state: State):
    current_plan = state.get("current_plan")
    if not current_plan or not current_plan.steps:
        return "planner"

    if all(step.execution_res for step in current_plan.steps):
        return "planner"

    # Find first incomplete step
    incomplete_step = None
    for step in current_plan.steps:
        if not step.execution_res:
            incomplete_step = step
            break

    if not incomplete_step:
        return "planner"

    if incomplete_step.step_type == StepType.RESEARCH:
        return "researcher"
    if incomplete_step.step_type == StepType.PROCESSING:
        return "coder"
    return "planner"


def _build_base_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)
    builder.add_edge(START, "coordinator")
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("research_team", research_team_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("coder", coder_node)
    builder.add_node("human_feedback", human_feedback_node)
    builder.add_edge("background_investigator", "planner")
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "coder"],
    )
    builder.add_edge("reporter", END)
    return builder


def _build_enhanced_graph():
    """Build and return the enhanced state graph with configurable node implementations."""
    
    # 创建一个包装函数来根据配置选择background investigation节点
    def configurable_background_investigation_node(state, config):
        if is_enhanced_background_investigation_enabled():
            return background_investigation_node_enhanced(state, config)
        else:
            return background_investigation_node(state, config)
    
    # 创建包装函数来根据配置选择researcher节点
    def configurable_researcher_node(state, config):
        if is_step_dependency_optimization_enabled():
            return researcher_node_with_dependencies(state, config)
        else:
            return researcher_node(state, config)
    
    # 创建包装函数来根据配置选择planner节点
    def configurable_planner_node(state, config):
        if is_step_dependency_optimization_enabled():
            return planner_node_with_dependencies(state, config)
        else:
            return planner_node(state, config)
    
    # 创建包装函数来根据配置选择coder节点
    def configurable_coder_node(state, config):
        if is_step_dependency_optimization_enabled():
            return coder_node_with_dependencies(state, config)
        else:
            return coder_node(state, config)
    
    builder = StateGraph(State)
    builder.add_edge(START, "coordinator")
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", configurable_background_investigation_node)
    builder.add_node("planner", configurable_planner_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("research_team", research_team_node)
    builder.add_node("researcher", configurable_researcher_node)
    builder.add_node("coder", configurable_coder_node)
    builder.add_node("human_feedback", human_feedback_node)
    builder.add_edge("background_investigator", "planner")
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "coder"],
    )
    builder.add_edge("reporter", END)
    return builder


def build_graph_with_memory():
    """Build and return the agent workflow graph with memory."""
    # use persistent memory to save conversation history
    # TODO: be compatible with SQLite / PostgreSQL
    memory = MemorySaver()

    # Check if any enhanced features are enabled
    if has_enhanced_features_enabled():
        # If enhanced features are enabled, use the enhanced graph builder
        builder = _build_enhanced_graph()
        return builder.compile(checkpointer=memory)

    # build state graph
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


def build_graph():
    """Build and return the agent workflow graph without memory."""

    # Check if any enhanced features are enabled
    if has_enhanced_features_enabled():
        # If enhanced features are enabled, use the enhanced graph builder
        builder = _build_enhanced_graph()
        return builder.compile()

    # build state graph
    builder = _build_base_graph()
    return builder.compile()


graph = build_graph()
