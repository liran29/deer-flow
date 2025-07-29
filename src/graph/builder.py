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

from .nodes_database import (
    database_investigation_node,
    database_planner_node,
    database_reporter_node,
    database_research_team_node,
    database_researcher_node,
)

from src.utils.enhanced_features import (
    is_enhanced_background_investigation_enabled,
    is_step_dependency_optimization_enabled,
    is_mindsdb_database_integration_enabled,
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


def continue_to_running_database_research_team(state: State):
    """数据库研究团队的条件路由函数"""
    current_plan = state.get("current_plan")
    if not current_plan or not current_plan.steps:
        return "reporter"

    # 检查是否所有步骤都已完成
    if all(step.execution_res for step in current_plan.steps):
        return "reporter"

    # 找到第一个未完成的步骤
    incomplete_step = None
    for step in current_plan.steps:
        if not step.execution_res:
            incomplete_step = step
            break

    if not incomplete_step:
        return "reporter"

    # 对于数据库分析，所有步骤都由researcher处理
    return "researcher"


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
    async def configurable_researcher_node(state, config):
        if is_step_dependency_optimization_enabled():
            return await researcher_node_with_dependencies(state, config)
        else:
            return await researcher_node(state, config)
    
    # 创建包装函数来根据配置选择planner节点
    def configurable_planner_node(state, config):
        if is_step_dependency_optimization_enabled():
            return planner_node_with_dependencies(state, config)
        else:
            return planner_node(state, config)
    
    # 创建包装函数来根据配置选择coder节点
    async def configurable_coder_node(state, config):
        if is_step_dependency_optimization_enabled():
            return await coder_node_with_dependencies(state, config)
        else:
            return await coder_node(state, config)
    
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
    
    # 只有background_investigator的传统流程
    builder.add_edge("background_investigator", "planner")
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "coder"],
    )
    builder.add_edge("reporter", END)
    return builder


def _build_database_graph():
    """Build and return the database investigation graph with research team."""
    builder = StateGraph(State)
    builder.add_edge(START, "coordinator")
    
    # 添加所有节点 - 使用与原版一致的节点名称
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", database_investigation_node)  # 用database_investigation替代background_investigator
    builder.add_node("planner", database_planner_node)  # 用database_planner替代原版planner
    builder.add_node("research_team", database_research_team_node)  # 用database_research_team替代原版research_team
    builder.add_node("researcher", database_researcher_node)  # 用database_researcher替代原版researcher
    builder.add_node("reporter", database_reporter_node)  # 用database_reporter替代原版reporter
    
    # 构建图的边 - 遵循原版流程但使用数据库节点
    builder.add_edge("background_investigator", "planner")  # 调查 -> 计划
    builder.add_edge("planner", "research_team")  # 计划 -> 研究团队
    
    # 条件边：根据步骤完成情况决定下一步
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_database_research_team,
        ["researcher", "reporter"],
    )
    
    # 执行完步骤后回到团队协调
    builder.add_edge("researcher", "research_team")
    
    # 最终生成报告
    builder.add_edge("reporter", END)
    
    return builder


def build_graph_with_memory():
    """Build and return the agent workflow graph with memory."""
    # use persistent memory to save conversation history
    # TODO: be compatible with SQLite / PostgreSQL
    memory = MemorySaver()

    # Check if any enhanced features are enabled
    if has_enhanced_features_enabled():
        # If MindsDB database integration is enabled, build the database graph
        if is_mindsdb_database_integration_enabled():
            return _build_database_graph().compile(checkpointer=memory)

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
        # If MindsDB database integration is enabled, build the database graph
        if is_mindsdb_database_integration_enabled():
            return _build_database_graph().compile()

        # If enhanced features are enabled, use the enhanced graph builder
        builder = _build_enhanced_graph()
        return builder.compile()

    # build state graph
    builder = _build_base_graph()
    return builder.compile()


graph = build_graph()
