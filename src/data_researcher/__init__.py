"""
本地数据驱动的深度研究员系统 (Local Data Deep-Researcher)

这是一个专门针对本地数据分析的智能研究系统，具备与deep-research相同的
智能规划和执行能力，但专注于数据挖掘和量化分析。

主要组件：
- DataIntentAnalyzer: 数据意图识别器
- DataExplorationPlanner: 数据探索规划器  
- SmartExecutionEngine: 智能执行引擎
- 专业分析代理团队
- 综合报告生成器
"""

from .intent_analyzer import DataIntentAnalyzer, DataAnalysisIntent
from .exploration_planner import DataExplorationPlanner, DataAnalysisPlan, AnalysisStep
# from .execution_engine import SmartExecutionEngine

__version__ = "1.0.0"
__all__ = [
    "DataIntentAnalyzer",
    "DataAnalysisIntent", 
    "DataExplorationPlanner",
    "DataAnalysisPlan",
    "AnalysisStep",
    # "SmartExecutionEngine"  # 待实现
]