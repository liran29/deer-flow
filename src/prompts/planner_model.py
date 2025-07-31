# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, validator


class StepType(str, Enum):
    RESEARCH = "research"
    PROCESSING = "processing"


class DependencyType(str, Enum):
    NONE = "none"          # No dependency, completely independent research
    SUMMARY = "summary"    # Only key findings and conclusions (recommended)
    KEY_POINTS = "key_points"  # Specific data points or metrics only
    FULL = "full"          # Complete detailed results (use sparingly to avoid token issues)


class ExecutionStatus(str, Enum):
    PENDING = "pending"           # Not yet executed
    COMPLETED = "completed"       # Successfully completed
    FAILED = "failed"            # Failed due to unexpected error
    SKIPPED = "skipped"          # Skipped due to content policy or other restrictions
    RATE_LIMITED = "rate_limited" # Failed due to API rate limits


class QueryStrategy(str, Enum):
    """Database query strategy types for optimization"""
    AGGREGATION = "aggregation"      # SQL aggregation functions (recommended for 90% cases)
    SAMPLING = "sampling"            # Limited data sampling for exploration
    PAGINATION = "pagination"        # Batch processing with summarization
    WINDOW_ANALYSIS = "window_analysis"  # Window functions for advanced analytics


class ResultSize(str, Enum):
    """Expected result size categories"""
    SINGLE_VALUE = "single_value"    # Single value or very few values
    SMALL_SET = "small_set"          # Small result set (< 100 rows)
    MEDIUM_SET = "medium_set"        # Medium result set (100-1000 rows)


class Step(BaseModel):
    need_search: bool = Field(..., description="Must be explicitly set for each step")
    title: str
    description: str = Field(..., description="Specify exactly what data to collect")
    step_type: StepType = Field(..., description="Indicates the nature of the step")
    execution_res: Optional[str] = Field(
        default=None, description="The Step execution result"
    )
    
    # Execution status and error tracking
    execution_status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING,
        description="Current execution status of this step"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if step failed or was skipped"
    )
    
    # New dependency fields for step optimization
    depends_on: List[int] = Field(
        default_factory=list, 
        description="Array of step indices (0-indexed) that this step needs information from"
    )
    dependency_type: DependencyType = Field(
        default=DependencyType.NONE,
        description="Level of detail needed from dependent steps"
    )
    required_info: List[str] = Field(
        default_factory=list,
        description="Specific information types needed when using 'key_points' dependency"
    )
    
    # Query optimization fields for database research
    query_strategy: QueryStrategy = Field(
        default=QueryStrategy.AGGREGATION,
        description="Database query strategy for optimal performance"
    )
    batch_size: Optional[int] = Field(
        default=None,
        description="Batch size for pagination or sampling (10-10000 range)"
    )
    max_batches: Optional[int] = Field(
        default=None,
        description="Maximum number of batches for pagination (1-100 range)"
    )
    sampling_rate: Optional[float] = Field(
        default=None,
        description="Sampling rate for statistical sampling (0.001-1.0 range)"
    )
    justification: str = Field(
        default="",
        description="Explanation for why this query strategy was chosen"
    )
    expected_result_size: ResultSize = Field(
        default=ResultSize.SMALL_SET,
        description="Expected size category of query results"
    )
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v is not None and (v < 10 or v > 10000):
            raise ValueError('batch_size must be between 10 and 10000')
        return v
    
    @validator('max_batches')
    def validate_max_batches(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('max_batches must be between 1 and 100')
        return v
    
    @validator('sampling_rate')
    def validate_sampling_rate(cls, v):
        if v is not None and (v < 0.001 or v > 1.0):
            raise ValueError('sampling_rate must be between 0.001 and 1.0')
        return v


class Plan(BaseModel):
    locale: str = Field(
        ..., description="e.g. 'en-US' or 'zh-CN', based on the user's language"
    )
    has_enough_context: bool
    thought: str
    title: str
    steps: List[Step] = Field(
        default_factory=list,
        description="Research & Processing steps to get more context",
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "has_enough_context": False,
                    "thought": (
                        "To understand the current market trends in AI, we need to gather comprehensive information."
                    ),
                    "title": "AI Market Research Plan",
                    "steps": [
                        {
                            "need_search": True,
                            "title": "Current AI Market Analysis",
                            "description": (
                                "Collect data on market size, growth rates, major players, and investment trends in AI sector."
                            ),
                            "step_type": "research",
                            "depends_on": [],
                            "dependency_type": "none",
                            "required_info": [],
                            "query_strategy": "aggregation",
                            "justification": "Statistical analysis of market trends using aggregation",
                            "expected_result_size": "small_set"
                        }
                    ],
                },
                {
                    "has_enough_context": False,
                    "thought": (
                        "To analyze 2024 order data comprehensively, we need statistical analysis rather than raw data viewing."
                    ),
                    "title": "2024 Order Data Analysis",
                    "steps": [
                        {
                            "need_search": False,
                            "title": "Order Overview Statistics",
                            "description": (
                                "Calculate total orders, total amount, and average order value for 2024"
                            ),
                            "step_type": "processing",
                            "query_strategy": "aggregation",
                            "justification": "Basic metrics using SQL aggregation functions",
                            "expected_result_size": "single_value"
                        },
                        {
                            "need_search": False,
                            "title": "Monthly Trend Analysis",
                            "description": (
                                "Analyze monthly distribution of orders and revenue in 2024"
                            ),
                            "step_type": "processing",
                            "query_strategy": "aggregation",
                            "justification": "Time series analysis with GROUP BY month",
                            "expected_result_size": "small_set"
                        },
                        {
                            "need_search": False,
                            "title": "Anomaly Detection Examples",
                            "description": (
                                "Find a few examples of unusually high or low value orders"
                            ),
                            "step_type": "processing",
                            "query_strategy": "sampling",
                            "batch_size": 10,
                            "justification": "Only need few examples for illustration",
                            "expected_result_size": "small_set"
                        }
                    ],
                }
            ]
        }
