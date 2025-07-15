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