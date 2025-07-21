# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class StepType(str, Enum):
    RESEARCH = "research"
    PROCESSING = "processing"


class DependencyType(str, Enum):
    NONE = "none"          # No dependency, completely independent research
    SUMMARY = "summary"    # Only key findings and conclusions (recommended)
    KEY_POINTS = "key_points"  # Specific data points or metrics only
    FULL = "full"          # Complete detailed results (use sparingly to avoid token issues)


class Step(BaseModel):
    need_search: bool = Field(..., description="Must be explicitly set for each step")
    title: str
    description: str = Field(..., description="Specify exactly what data to collect")
    step_type: StepType = Field(..., description="Indicates the nature of the step")
    execution_res: Optional[str] = Field(
        default=None, description="The Step execution result"
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
                            "required_info": []
                        }
                    ],
                }
            ]
        }
