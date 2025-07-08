"""
Test suite for TokenComparisonLogger functionality.
"""

import os
import json
import pytest
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.utils.token_comparison_logger import TokenComparisonLogger, load_comparison_logger_from_config


class TestTokenComparisonLogger:
    """Test cases for TokenComparisonLogger."""
    
    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary output directory for tests."""
        return str(tmp_path / "token_comparisons")
    
    @pytest.fixture
    def logger(self, temp_output_dir):
        """Create a test logger instance."""
        return TokenComparisonLogger(
            enabled=True,
            output_dir=temp_output_dir,
            max_content_preview=100,
            save_full_content=True
        )
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for testing."""
        return [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Tell me about the history of computers."),
            AIMessage(content="The history of computers dates back to ancient times with devices like the abacus..."),
            HumanMessage(content="What about modern computers?"),
            AIMessage(content="Modern computers began with Charles Babbage's Analytical Engine in the 1830s..."),
            HumanMessage(content="Tell me more about transistors."),
            AIMessage(content="Transistors, invented in 1947 at Bell Labs, revolutionized computing..."),
        ]
    
    def test_logger_initialization(self, logger, temp_output_dir):
        """Test logger initialization and directory creation."""
        assert logger.enabled is True
        assert str(logger.output_dir) == temp_output_dir
        
        # Check subdirectories were created
        assert (Path(temp_output_dir) / "json").exists()
        assert (Path(temp_output_dir) / "markdown").exists()
        assert (Path(temp_output_dir) / "summary").exists()
    
    def test_disabled_logger(self, temp_output_dir):
        """Test that disabled logger doesn't create files."""
        logger = TokenComparisonLogger(enabled=False, output_dir=temp_output_dir)
        
        result = logger.log_comparison(
            original_messages=[HumanMessage(content="test")],
            trimmed_messages=[],
            node_name="test",
            model_name="test-model",
            max_tokens=1000,
            strategy={"strategy": "last"}
        )
        
        assert result is None
        assert not Path(temp_output_dir).exists()
    
    def test_log_comparison_basic(self, logger, sample_messages, temp_output_dir):
        """Test basic comparison logging."""
        # Simulate trimming - remove middle messages
        trimmed_messages = [sample_messages[0], sample_messages[-2], sample_messages[-1]]
        
        result = logger.log_comparison(
            original_messages=sample_messages,
            trimmed_messages=trimmed_messages,
            node_name="test_node",
            model_name="test-model",
            max_tokens=1000,
            strategy={"strategy": "last", "include_system": True},
            token_counts={"original": 500, "trimmed": 200}
        )
        
        assert result is not None
        assert "test_node" in result
        assert result.endswith(".md")
        
        # Check files were created
        json_files = list((Path(temp_output_dir) / "json").glob("*.json"))
        assert len(json_files) == 1
        
        markdown_files = list((Path(temp_output_dir) / "markdown").glob("*.md"))
        assert len(markdown_files) == 1
    
    def test_comparison_data_structure(self, logger, sample_messages, temp_output_dir):
        """Test the structure of saved comparison data."""
        trimmed_messages = sample_messages[:3]  # Keep first 3 messages
        
        logger.log_comparison(
            original_messages=sample_messages,
            trimmed_messages=trimmed_messages,
            node_name="planner",
            model_name="deepseek-chat",
            max_tokens=2000,
            strategy={"strategy": "first"},
            token_counts={"original": 1000, "trimmed": 400}
        )
        
        # Load the JSON file
        json_file = list((Path(temp_output_dir) / "json").glob("*.json"))[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check metadata
        assert data["metadata"]["node_name"] == "planner"
        assert data["metadata"]["model_name"] == "deepseek-chat"
        assert data["metadata"]["max_tokens"] == 2000
        
        # Check statistics
        assert data["statistics"]["original_message_count"] == 7
        assert data["statistics"]["trimmed_message_count"] == 3
        assert data["statistics"]["messages_removed"] == 4
        assert data["statistics"]["original_tokens"] == 1000
        assert data["statistics"]["trimmed_tokens"] == 400
        assert data["statistics"]["tokens_saved"] == 600
        assert data["statistics"]["reduction_percentage"] == 60.0
        
        # Check messages
        assert len(data["messages"]["original"]) == 7
        assert len(data["messages"]["trimmed"]) == 3
        assert len(data["messages"]["removed_indices"]) == 4
    
    def test_message_preview_truncation(self, logger, temp_output_dir):
        """Test that long messages are truncated in preview."""
        long_content = "A" * 200  # Longer than max_content_preview (100)
        messages = [HumanMessage(content=long_content)]
        
        logger.log_comparison(
            original_messages=messages,
            trimmed_messages=messages,
            node_name="test",
            model_name="test",
            max_tokens=1000,
            strategy={}
        )
        
        json_file = list((Path(temp_output_dir) / "json").glob("*.json"))[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check preview is truncated
        preview = data["messages"]["original"][0]["preview"]
        assert len(preview) == 103  # 100 + "..."
        assert preview.endswith("...")
        
        # Check full content is saved
        assert data["messages"]["original"][0]["full_content"] == long_content
    
    def test_summary_update(self, logger, sample_messages, temp_output_dir):
        """Test that summary file is updated correctly."""
        # Log multiple comparisons
        for i in range(3):
            logger.log_comparison(
                original_messages=sample_messages,
                trimmed_messages=sample_messages[:3],
                node_name=f"node_{i}",
                model_name="test-model",
                max_tokens=1000,
                strategy={},
                token_counts={"original": 1000, "trimmed": 600}
            )
        
        # Check summary file
        summary_path = Path(temp_output_dir) / "summary" / "trimming_summary.json"
        assert summary_path.exists()
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        assert summary["total_comparisons"] == 3
        assert summary["total_tokens_saved"] == 1200  # 400 * 3
        assert len(summary["by_node"]) == 3
    
    def test_markdown_report_format(self, logger, sample_messages, temp_output_dir):
        """Test the markdown report format."""
        trimmed_messages = [sample_messages[0], sample_messages[-1]]
        
        logger.log_comparison(
            original_messages=sample_messages,
            trimmed_messages=trimmed_messages,
            node_name="reporter",
            model_name="gemini-flash",
            max_tokens=5000,
            strategy={"strategy": "last", "include_system": True}
        )
        
        # Read markdown file
        md_file = list((Path(temp_output_dir) / "markdown").glob("*.md"))[0]
        with open(md_file, 'r') as f:
            content = f.read()
        
        # Check key sections exist
        assert "# Token Trimming Comparison Report" in content
        assert "## Configuration" in content
        assert "## Statistics" in content
        assert "## Trimming Analysis" in content
        assert "## Message Comparison" in content
        assert "### Original Messages" in content
        assert "### Trimmed Messages" in content
        
        # Check removed messages are marked
        assert "❌" in content  # Removed message marker
    
    def test_html_generation(self, logger, sample_messages, temp_output_dir):
        """Test HTML report generation."""
        logger.log_comparison(
            original_messages=sample_messages,
            trimmed_messages=sample_messages[:2],
            node_name="test",
            model_name="test",
            max_tokens=1000,
            strategy={}
        )
        
        # Get the JSON file
        json_file = list((Path(temp_output_dir) / "json").glob("*.json"))[0]
        
        # Generate HTML
        html_path = logger.generate_html_report(str(json_file))
        assert html_path is not None
        assert Path(html_path).exists()
        
        # Check HTML content
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        assert "<title>Token Trimming Comparison" in html_content
        assert "Original Messages" in html_content
        assert "Trimmed Messages" in html_content
    
    def test_load_from_config(self, tmp_path):
        """Test loading logger from configuration."""
        # Create a test config
        config_content = """
TOKEN_MANAGEMENT:
  enabled: true
  debug:
    enabled: true
    output_dir: "test_output"
    max_content_preview: 200
    save_full_content: false
"""
        config_path = tmp_path / "test_conf.yaml"
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Load logger
        logger = load_comparison_logger_from_config(str(config_path))
        
        assert logger.enabled is True
        assert logger.max_content_preview == 200
        assert logger.save_full_content is False
    
    def test_removed_message_identification(self, logger):
        """Test correct identification of removed messages."""
        original = [
            HumanMessage(content="A"),
            AIMessage(content="B"),
            HumanMessage(content="C"),
            AIMessage(content="D"),
            HumanMessage(content="E"),
        ]
        
        # Remove messages at indices 1 and 3
        trimmed = [original[0], original[2], original[4]]
        
        removed_indices = logger._identify_removed_messages(original, trimmed)
        assert removed_indices == [1, 3]
    
    def test_trimming_pattern_analysis(self, logger):
        """Test analysis of trimming patterns."""
        original = [
            SystemMessage(content="System"),
            HumanMessage(content="1"),
            AIMessage(content="2"),
            HumanMessage(content="3"),
            AIMessage(content="4"),
        ]
        
        # Test beginning removal
        trimmed = original[2:]
        analysis = logger._analyze_trimming_pattern(
            original, trimmed, [0, 1], {"strategy": "last"}
        )
        assert analysis["removed_from"] == "beginning"
        
        # Test end removal
        trimmed = original[:3]
        analysis = logger._analyze_trimming_pattern(
            original, trimmed, [3, 4], {"strategy": "first"}
        )
        assert analysis["removed_from"] == "end"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])