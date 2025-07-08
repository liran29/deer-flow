"""
Debug logger for token management analysis.
Provides file logging capabilities for debugging token-related issues.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List


class DebugFileLogger:
    """A debug logger that saves logs to file for analysis."""
    
    def __init__(self, log_name: str = "token_management", log_dir: str = "logs/debug"):
        """
        Initialize debug file logger.
        
        Args:
            log_name: Base name for log file
            log_dir: Directory to save log files
        """
        self.log_name = log_name
        self.log_dir = log_dir
        self.file_handler: Optional[logging.FileHandler] = None
        self.attached_loggers: List[logging.Logger] = []
        
    def start_session(self, session_name: Optional[str] = None) -> str:
        """
        Start a new debug logging session.
        
        Args:
            session_name: Optional name for the session
            
        Returns:
            Path to the log file
        """
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Generate log file name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if session_name:
            filename = f"{self.log_name}_{session_name}_{timestamp}.log"
        else:
            filename = f"{self.log_name}_{timestamp}.log"
        
        self.log_path = os.path.join(self.log_dir, filename)
        
        # Create file handler
        self.file_handler = logging.FileHandler(self.log_path, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)
        
        # Set formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        
        # Write session header
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"Debug Logging Session: {session_name or 'default'}\n")
            f.write(f"Started at: {datetime.now()}\n")
            f.write(f"{'='*60}\n\n")
        
        return self.log_path
    
    def attach_logger(self, logger_name: str) -> None:
        """
        Attach file handler to a specific logger.
        
        Args:
            logger_name: Name of the logger to attach to
        """
        if not self.file_handler:
            raise RuntimeError("No active session. Call start_session() first.")
        
        logger = logging.getLogger(logger_name)
        logger.addHandler(self.file_handler)
        self.attached_loggers.append(logger)
        
        # Log attachment
        logger.debug(f"Logger '{logger_name}' attached to debug file: {self.log_path}")
    
    def attach_multiple_loggers(self, logger_names: List[str]) -> None:
        """
        Attach file handler to multiple loggers.
        
        Args:
            logger_names: List of logger names to attach to
        """
        for name in logger_names:
            self.attach_logger(name)
    
    def detach_all(self) -> None:
        """Detach file handler from all loggers."""
        if self.file_handler:
            for logger in self.attached_loggers:
                logger.removeHandler(self.file_handler)
            self.file_handler.close()
            self.file_handler = None
            self.attached_loggers.clear()
    
    def log_section(self, title: str, content: str) -> None:
        """
        Write a formatted section to the log file.
        
        Args:
            title: Section title
            content: Section content
        """
        if not self.log_path:
            return
            
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*40}\n")
            f.write(f"{title}\n")
            f.write(f"{'='*40}\n")
            f.write(f"{content}\n")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - detach all loggers."""
        self.detach_all()


# Global instance for easy access
_debug_logger: Optional[DebugFileLogger] = None


def start_debug_logging(session_name: Optional[str] = None, 
                       loggers: Optional[List[str]] = None) -> DebugFileLogger:
    """
    Start a debug logging session.
    
    Args:
        session_name: Optional name for the session
        loggers: List of logger names to attach to
        
    Returns:
        DebugFileLogger instance
    """
    global _debug_logger
    
    # Default loggers for token management debugging
    if loggers is None:
        loggers = [
            "src.graph.nodes",
            "src.utils.token_manager", 
            "src.utils.token_counter",
            "src.utils.token_comparison_logger",
            "src.agents.agents",
            "langgraph.pregel",
            "httpx"  # To capture API errors
        ]
    
    _debug_logger = DebugFileLogger()
    log_path = _debug_logger.start_session(session_name)
    _debug_logger.attach_multiple_loggers(loggers)
    
    # Log initial info
    logger = logging.getLogger("src.utils.debug_logger")
    logger.info(f"Debug logging started. Log file: {log_path}")
    logger.info(f"Attached loggers: {', '.join(loggers)}")
    
    return _debug_logger


def stop_debug_logging() -> None:
    """Stop the current debug logging session."""
    global _debug_logger
    if _debug_logger:
        _debug_logger.detach_all()
        _debug_logger = None


def get_debug_logger() -> Optional[DebugFileLogger]:
    """Get the current debug logger instance."""
    return _debug_logger