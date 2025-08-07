# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from pathlib import Path
from src.config import load_yaml_config


def _get_config_file_path() -> str:
    """Get the path to the configuration file."""
    return str((Path(__file__).parent.parent.parent / "conf.yaml").resolve())


def get_enhanced_features_config() -> dict:
    """Get enhanced features configuration from conf.yaml"""
    config = load_yaml_config(_get_config_file_path())
    return config.get("ENHANCED_FEATURES", {})


def is_enhanced_background_investigation_enabled() -> bool:
    """Check if enhanced background investigation is enabled"""
    enhanced_config = get_enhanced_features_config()
    return enhanced_config.get("enhanced_background_investigation", False)

def is_step_dependency_optimization_enabled() -> bool:
    """Check if step dependency optimization is enabled
    
    This feature optimizes token usage by only passing relevant information
    from previous steps based on declared dependencies, instead of blindly
    accumulating all previous step results.
    """
    enhanced_config = get_enhanced_features_config()
    return enhanced_config.get("step_dependency_optimization", False)


def is_mindsdb_database_integration_enabled() -> bool:
    """Check if MindsDB database integration is enabled
    
    This feature provides local database querying capabilities to agents,
    allowing them to access structured data directly from MindsDB-connected
    databases instead of relying solely on web search.
    """
    enhanced_config = get_enhanced_features_config()
    return enhanced_config.get("mindsdb_database_integration", False)


def is_background_investigation_domain_filter_enabled() -> bool:
    """Check if background investigation should use domain filter
    
    This feature controls whether background investigation respects the
    include_domains configuration. When enabled, background investigation
    will only search within configured domains. When disabled, it searches
    all domains to get broader background information.
    """
    enhanced_config = get_enhanced_features_config()
    return enhanced_config.get("background_investigation_use_domain_filter", True)


def is_background_investigation_query_optimization_enabled() -> bool:
    """Check if background investigation should use query optimization
    
    This feature enables automatic query optimization for background investigation,
    including Chinese-to-English translation and keyword extraction for better
    search results.
    """
    enhanced_config = get_enhanced_features_config()
    return enhanced_config.get("background_investigation_query_optimization", True)


def is_researcher_query_optimization_enabled() -> bool:
    """Check if researcher node should use query optimization
    
    This feature enables automatic query optimization for researcher nodes,
    improving search quality for complex or non-English queries.
    """
    enhanced_config = get_enhanced_features_config()
    return enhanced_config.get("researcher_query_optimization", True)


def has_enhanced_features_enabled() -> bool:
    """Check if any enhanced features are enabled"""
    enhanced_config = get_enhanced_features_config()

    # Check if any key in the enhanced features config is set to True
    for key, value in enhanced_config.items():
        if isinstance(value, bool) and value:
            return True
        if isinstance(value, dict) and any(v is True for v in value.values()):
            return True
    return False