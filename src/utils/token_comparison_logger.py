"""
Token Comparison Logger for debugging and analyzing message trimming.

This module provides functionality to save and display before/after comparisons
of trimmed messages, helping developers understand what trim_messages actually does.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
import yaml

logger = logging.getLogger(__name__)


class TokenComparisonLogger:
    """
    Logger for saving and displaying token trimming comparisons.
    
    This class provides functionality to:
    1. Save before/after message comparisons to files
    2. Generate human-readable comparison reports
    3. Track token counts and reduction statistics
    4. Create visualizations of what was trimmed
    """
    
    def __init__(self, 
                 enabled: bool = False,
                 output_dir: str = "logs/token_comparisons",
                 max_content_preview: int = 500,
                 save_full_content: bool = True):
        """
        Initialize the TokenComparisonLogger.
        
        Args:
            enabled: Whether to enable logging (default: False for production)
            output_dir: Directory to save comparison files
            max_content_preview: Maximum characters to show in preview
            save_full_content: Whether to save full message content
        """
        self.enabled = enabled
        self.output_dir = Path(output_dir)
        self.max_content_preview = max_content_preview
        self.save_full_content = save_full_content
        
        if self.enabled:
            self._ensure_output_dir()
            logger.info(f"TokenComparisonLogger enabled. Output directory: {self.output_dir}")
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.output_dir / "json").mkdir(exist_ok=True)
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "summary").mkdir(exist_ok=True)
    
    def log_comparison(self,
                      original_messages: List[BaseMessage],
                      trimmed_messages: List[BaseMessage],
                      node_name: str,
                      model_name: str,
                      max_tokens: int,
                      strategy: Dict[str, Any],
                      token_counts: Optional[Dict[str, int]] = None) -> Optional[str]:
        """
        Log a before/after comparison of message trimming.
        
        Args:
            original_messages: Original messages before trimming
            trimmed_messages: Messages after trimming
            node_name: Name of the workflow node
            model_name: Name of the model
            max_tokens: Maximum token limit applied
            strategy: Trimming strategy configuration
            token_counts: Optional dictionary with 'original' and 'trimmed' token counts
            
        Returns:
            Path to the saved comparison file, or None if logging is disabled
        """
        if not self.enabled:
            return None
        
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{node_name}_{model_name}_{timestamp}"
            
            # Prepare comparison data
            comparison_data = self._prepare_comparison_data(
                original_messages,
                trimmed_messages,
                node_name,
                model_name,
                max_tokens,
                strategy,
                token_counts
            )
            
            # Save in multiple formats
            json_path = self._save_json_comparison(base_filename, comparison_data)
            markdown_path = self._save_markdown_comparison(base_filename, comparison_data)
            
            # Update summary file
            self._update_summary(comparison_data)
            
            logger.info(f"Token comparison saved: {markdown_path}")
            return str(markdown_path)
            
        except Exception as e:
            logger.error(f"Failed to log token comparison: {e}")
            return None
    
    def _prepare_comparison_data(self,
                                original_messages: List[BaseMessage],
                                trimmed_messages: List[BaseMessage],
                                node_name: str,
                                model_name: str,
                                max_tokens: int,
                                strategy: Dict[str, Any],
                                token_counts: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Prepare structured comparison data."""
        # Calculate basic statistics
        messages_removed = len(original_messages) - len(trimmed_messages)
        
        # Identify which messages were removed
        removed_indices = self._identify_removed_messages(original_messages, trimmed_messages)
        
        # Prepare message details
        original_details = [self._message_to_dict(msg, idx) for idx, msg in enumerate(original_messages)]
        trimmed_details = [self._message_to_dict(msg, idx) for idx, msg in enumerate(trimmed_messages)]
        
        # Calculate token statistics
        if token_counts:
            original_tokens = token_counts.get('original', 0)
            trimmed_tokens = token_counts.get('trimmed', 0)
        else:
            # Rough estimation based on content length
            original_tokens = sum(len(str(msg.content)) for msg in original_messages) // 4
            trimmed_tokens = sum(len(str(msg.content)) for msg in trimmed_messages) // 4
        
        tokens_saved = original_tokens - trimmed_tokens
        reduction_percentage = (tokens_saved / original_tokens * 100) if original_tokens > 0 else 0
        
        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "node_name": node_name,
                "model_name": model_name,
                "max_tokens": max_tokens,
                "strategy": strategy,
            },
            "statistics": {
                "original_message_count": len(original_messages),
                "trimmed_message_count": len(trimmed_messages),
                "messages_removed": messages_removed,
                "original_tokens": original_tokens,
                "trimmed_tokens": trimmed_tokens,
                "tokens_saved": tokens_saved,
                "reduction_percentage": reduction_percentage,
            },
            "messages": {
                "original": original_details,
                "trimmed": trimmed_details,
                "removed_indices": removed_indices,
            },
            "trimming_analysis": self._analyze_trimming_pattern(
                original_messages, trimmed_messages, removed_indices, strategy
            )
        }
    
    def _message_to_dict(self, message: BaseMessage, index: int) -> Dict[str, Any]:
        """Convert a message to a dictionary with metadata."""
        content = str(message.content)
        
        # Determine message type
        message_type = message.__class__.__name__
        
        # Create preview
        preview = content[:self.max_content_preview]
        if len(content) > self.max_content_preview:
            preview += "..."
        
        result = {
            "index": index,
            "type": message_type,
            "content_length": len(content),
            "preview": preview,
        }
        
        # Include full content if enabled
        if self.save_full_content:
            result["full_content"] = content
        
        # Add any additional metadata
        if hasattr(message, 'name') and message.name:
            result["name"] = message.name
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            result["has_tool_calls"] = True
            result["tool_call_count"] = len(message.tool_calls)
        
        return result
    
    def _identify_removed_messages(self, 
                                  original: List[BaseMessage], 
                                  trimmed: List[BaseMessage]) -> List[int]:
        """Identify which messages were removed during trimming."""
        removed_indices = []
        
        # Simple approach: check if messages are in the same order
        trimmed_idx = 0
        for orig_idx, orig_msg in enumerate(original):
            if trimmed_idx < len(trimmed):
                # Check if content matches
                if str(orig_msg.content) == str(trimmed[trimmed_idx].content):
                    trimmed_idx += 1
                else:
                    removed_indices.append(orig_idx)
            else:
                removed_indices.append(orig_idx)
        
        return removed_indices
    
    def _analyze_trimming_pattern(self,
                                 original: List[BaseMessage],
                                 trimmed: List[BaseMessage],
                                 removed_indices: List[int],
                                 strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the pattern of message trimming."""
        analysis = {
            "strategy_used": strategy.get("strategy", "unknown"),
            "removed_from": "unknown",
            "preserved_message_types": {},
            "removed_message_types": {},
        }
        
        if not removed_indices:
            analysis["removed_from"] = "none"
            return analysis
        
        # Determine where messages were removed from
        if removed_indices == list(range(len(removed_indices))):
            analysis["removed_from"] = "beginning"
        elif removed_indices == list(range(len(original) - len(removed_indices), len(original))):
            analysis["removed_from"] = "end"
        else:
            analysis["removed_from"] = "middle_or_mixed"
        
        # Analyze message types
        for idx, msg in enumerate(original):
            msg_type = msg.__class__.__name__
            if idx in removed_indices:
                analysis["removed_message_types"][msg_type] = \
                    analysis["removed_message_types"].get(msg_type, 0) + 1
            else:
                analysis["preserved_message_types"][msg_type] = \
                    analysis["preserved_message_types"].get(msg_type, 0) + 1
        
        return analysis
    
    def _save_json_comparison(self, base_filename: str, data: Dict[str, Any]) -> str:
        """Save comparison data as JSON."""
        json_path = self.output_dir / "json" / f"{base_filename}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(json_path)
    
    def _save_markdown_comparison(self, base_filename: str, data: Dict[str, Any]) -> str:
        """Save comparison data as a readable Markdown report."""
        markdown_path = self.output_dir / "markdown" / f"{base_filename}.md"
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Token Trimming Comparison Report\n\n")
            f.write(f"**Generated:** {data['metadata']['timestamp']}\n\n")
            
            # Metadata
            f.write("## Configuration\n\n")
            f.write(f"- **Node:** {data['metadata']['node_name']}\n")
            f.write(f"- **Model:** {data['metadata']['model_name']}\n")
            f.write(f"- **Max Tokens:** {data['metadata']['max_tokens']:,}\n")
            f.write(f"- **Strategy:** {data['metadata']['strategy']}\n\n")
            
            # Statistics
            f.write("## Statistics\n\n")
            stats = data['statistics']
            f.write(f"- **Messages:** {stats['original_message_count']} → {stats['trimmed_message_count']} ")
            f.write(f"({stats['messages_removed']} removed)\n")
            f.write(f"- **Tokens:** {stats['original_tokens']:,} → {stats['trimmed_tokens']:,} ")
            f.write(f"({stats['tokens_saved']:,} saved, {stats['reduction_percentage']:.1f}% reduction)\n\n")
            
            # Trimming Analysis
            f.write("## Trimming Analysis\n\n")
            analysis = data['trimming_analysis']
            f.write(f"- **Strategy Used:** {analysis['strategy_used']}\n")
            f.write(f"- **Removed From:** {analysis['removed_from']}\n")
            f.write(f"- **Preserved Types:** {analysis['preserved_message_types']}\n")
            f.write(f"- **Removed Types:** {analysis['removed_message_types']}\n\n")
            
            # Message Comparison
            f.write("## Message Comparison\n\n")
            
            # Original Messages
            f.write("### Original Messages\n\n")
            for msg in data['messages']['original']:
                removed_marker = " ❌" if msg['index'] in data['messages']['removed_indices'] else ""
                f.write(f"**[{msg['index']}] {msg['type']}{removed_marker}** ")
                f.write(f"({msg['content_length']} chars)\n")
                f.write(f"```\n{msg['preview']}\n```\n\n")
            
            # Trimmed Messages
            f.write("### Trimmed Messages\n\n")
            for msg in data['messages']['trimmed']:
                f.write(f"**[{msg['index']}] {msg['type']}** ")
                f.write(f"({msg['content_length']} chars)\n")
                f.write(f"```\n{msg['preview']}\n```\n\n")
            
            # Removed Messages Detail
            if data['messages']['removed_indices']:
                f.write("### Removed Messages Detail\n\n")
                for idx in data['messages']['removed_indices']:
                    msg = data['messages']['original'][idx]
                    f.write(f"**Message {idx} ({msg['type']}):**\n")
                    if self.save_full_content and 'full_content' in msg:
                        content = msg['full_content']
                        if len(content) > 1000:
                            f.write(f"```\n{content[:1000]}\n... (truncated)\n```\n\n")
                        else:
                            f.write(f"```\n{content}\n```\n\n")
                    else:
                        f.write(f"```\n{msg['preview']}\n```\n\n")
        
        return str(markdown_path)
    
    def _update_summary(self, data: Dict[str, Any]):
        """Update the running summary file with this comparison."""
        summary_path = self.output_dir / "summary" / "trimming_summary.json"
        
        # Load existing summary or create new
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                summary = json.load(f)
        else:
            summary = {
                "total_comparisons": 0,
                "total_tokens_saved": 0,
                "average_reduction_percentage": 0,
                "by_node": {},
                "by_model": {},
            }
        
        # Update summary statistics
        summary["total_comparisons"] += 1
        summary["total_tokens_saved"] += data['statistics']['tokens_saved']
        
        # Update per-node statistics
        node_name = data['metadata']['node_name']
        if node_name not in summary["by_node"]:
            summary["by_node"][node_name] = {
                "comparisons": 0,
                "total_tokens_saved": 0,
                "average_reduction": 0,
            }
        
        summary["by_node"][node_name]["comparisons"] += 1
        summary["by_node"][node_name]["total_tokens_saved"] += data['statistics']['tokens_saved']
        
        # Recalculate averages
        total_reduction = 0
        for node_data in summary["by_node"].values():
            if node_data["comparisons"] > 0:
                total_reduction += node_data.get("average_reduction", 0)
        
        if summary["total_comparisons"] > 0:
            summary["average_reduction_percentage"] = total_reduction / len(summary["by_node"])
        
        # Save updated summary
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def generate_html_report(self, comparison_file: str) -> str:
        """
        Generate an interactive HTML report from a comparison file.
        
        Args:
            comparison_file: Path to the JSON comparison file
            
        Returns:
            Path to the generated HTML file
        """
        if not self.enabled:
            return None
        
        # Load comparison data
        with open(comparison_file, 'r') as f:
            data = json.load(f)
        
        # Generate HTML
        html_content = self._generate_html_content(data)
        
        # Save HTML file
        html_filename = Path(comparison_file).stem + ".html"
        html_path = self.output_dir / "html" / html_filename
        html_path.parent.mkdir(exist_ok=True)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_path)
    
    def _generate_html_content(self, data: Dict[str, Any]) -> str:
        """Generate HTML content for visualization."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Token Trimming Comparison - {data['metadata']['node_name']}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                .stat-label {{
                    color: #666;
                    font-size: 14px;
                }}
                .comparison {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-top: 30px;
                }}
                .message-list {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                }}
                .message {{
                    margin-bottom: 15px;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}
                .message.removed {{
                    background-color: #ffe0e0;
                    border: 1px solid #ffcccc;
                }}
                .message-header {{
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .message-content {{
                    font-family: monospace;
                    font-size: 12px;
                    white-space: pre-wrap;
                    word-break: break-all;
                }}
                .reduction-bar {{
                    width: 100%;
                    height: 30px;
                    background-color: #e0e0e0;
                    border-radius: 4px;
                    overflow: hidden;
                    margin: 20px 0;
                }}
                .reduction-fill {{
                    height: 100%;
                    background-color: #4caf50;
                    transition: width 1s ease;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Token Trimming Comparison</h1>
                <p><strong>Node:</strong> {data['metadata']['node_name']} | 
                   <strong>Model:</strong> {data['metadata']['model_name']} | 
                   <strong>Time:</strong> {data['metadata']['timestamp']}</p>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">{data['statistics']['original_message_count']}</div>
                        <div class="stat-label">Original Messages</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{data['statistics']['trimmed_message_count']}</div>
                        <div class="stat-label">Trimmed Messages</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{data['statistics']['tokens_saved']:,}</div>
                        <div class="stat-label">Tokens Saved</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{data['statistics']['reduction_percentage']:.1f}%</div>
                        <div class="stat-label">Reduction</div>
                    </div>
                </div>
                
                <div class="reduction-bar">
                    <div class="reduction-fill" style="width: {data['statistics']['reduction_percentage']}%"></div>
                </div>
                
                <div class="comparison">
                    <div class="message-list">
                        <h2>Original Messages</h2>
                        {self._generate_message_html(data['messages']['original'], data['messages']['removed_indices'])}
                    </div>
                    <div class="message-list">
                        <h2>Trimmed Messages</h2>
                        {self._generate_message_html(data['messages']['trimmed'], [])}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_message_html(self, messages: List[Dict], removed_indices: List[int]) -> str:
        """Generate HTML for message list."""
        html_parts = []
        for msg in messages:
            removed_class = "removed" if msg['index'] in removed_indices else ""
            html_parts.append(f"""
                <div class="message {removed_class}">
                    <div class="message-header">
                        [{msg['index']}] {msg['type']} ({msg['content_length']} chars)
                    </div>
                    <div class="message-content">{msg['preview']}</div>
                </div>
            """)
        return "\n".join(html_parts)


def load_comparison_logger_from_config(config_path: str = "conf.yaml") -> TokenComparisonLogger:
    """
    Load TokenComparisonLogger with settings from configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured TokenComparisonLogger instance
    """
    try:
        # Load configuration
        if not os.path.isabs(config_path):
            project_root = Path(__file__).parent.parent.parent
            config_path = (project_root / config_path).resolve()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Get token comparison settings
        token_management = config.get("TOKEN_MANAGEMENT", {})
        debug_config = token_management.get("debug", {})
        
        return TokenComparisonLogger(
            enabled=debug_config.get("enabled", False),
            output_dir=debug_config.get("output_dir", "logs/token_comparisons"),
            max_content_preview=debug_config.get("max_content_preview", 500),
            save_full_content=debug_config.get("save_full_content", True)
        )
        
    except Exception as e:
        logger.warning(f"Failed to load comparison logger config: {e}. Using defaults.")
        return TokenComparisonLogger(enabled=False)