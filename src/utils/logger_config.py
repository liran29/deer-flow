"""
Global logger configuration for deer-flow.
Provides easy way to enable/disable file logging for all loggers.
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """Manage global logger configuration."""
    
    _file_handler: Optional[logging.FileHandler] = None
    _log_file_path: Optional[str] = None
    
    @classmethod
    def enable_file_logging(cls, 
                          log_dir: str = "logs",
                          log_filename: Optional[str] = None,
                          level: int = logging.DEBUG) -> str:
        """
        Enable file logging for all loggers.
        
        Args:
            log_dir: Directory to save log files
            log_filename: Optional custom filename, otherwise auto-generated
            level: Logging level for file handler
            
        Returns:
            Path to the log file
        """
        # Disable existing file handler if any
        if cls._file_handler:
            cls.disable_file_logging()
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate filename if not provided
        if log_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"deer_flow_{timestamp}.log"
        
        cls._log_file_path = os.path.join(log_dir, log_filename)
        
        # Create file handler
        cls._file_handler = logging.FileHandler(cls._log_file_path, encoding='utf-8')
        cls._file_handler.setLevel(level)
        
        # Set formatter to match console output
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        cls._file_handler.setFormatter(formatter)
        
        # Add handler to root logger - this affects all loggers
        root_logger = logging.getLogger()
        root_logger.addHandler(cls._file_handler)
        
        # Also set root logger level if needed
        if root_logger.level > level:
            root_logger.setLevel(level)
        
        # Write header to log file
        with open(cls._log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Logging session started at: {datetime.now()}\n")
            f.write(f"Log level: {logging.getLevelName(level)}\n")
            f.write(f"{'='*60}\n\n")
        
        return cls._log_file_path
    
    @classmethod
    def disable_file_logging(cls) -> None:
        """Disable file logging."""
        if cls._file_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(cls._file_handler)
            cls._file_handler.close()
            cls._file_handler = None
            cls._log_file_path = None
    
    @classmethod
    def is_file_logging_enabled(cls) -> bool:
        """Check if file logging is currently enabled."""
        return cls._file_handler is not None
    
    @classmethod
    def get_log_file_path(cls) -> Optional[str]:
        """Get current log file path."""
        return cls._log_file_path
    
    @classmethod
    def set_console_level(cls, level: int) -> None:
        """
        Set logging level for console output.
        
        Args:
            level: Logging level (e.g., logging.INFO, logging.DEBUG)
        """
        # Find console handler and update its level
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
                break
    
    @classmethod
    def set_file_level(cls, level: int) -> None:
        """
        Set logging level for file output.
        
        Args:
            level: Logging level
        """
        if cls._file_handler:
            cls._file_handler.setLevel(level)


# Convenience functions
def enable_debug_file_logging(filename: Optional[str] = None) -> str:
    """
    Enable debug file logging with a single function call.
    
    Args:
        filename: Optional custom filename
        
    Returns:
        Path to the log file
    """
    return LoggerConfig.enable_file_logging(
        log_dir="logs/debug",
        log_filename=filename,
        level=logging.DEBUG
    )


def enable_file_logging(filename: Optional[str] = None) -> str:
    """
    Enable info-level file logging.
    
    Args:
        filename: Optional custom filename
        
    Returns:
        Path to the log file
    """
    return LoggerConfig.enable_file_logging(
        log_dir="logs",
        log_filename=filename,
        level=logging.INFO
    )


def disable_file_logging() -> None:
    """Disable file logging."""
    LoggerConfig.disable_file_logging()