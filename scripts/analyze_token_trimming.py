#!/usr/bin/env python3
"""
Utility script to analyze token trimming comparisons.

This script provides commands to:
- Enable/disable token comparison logging
- View saved comparisons
- Generate summary reports
- Convert comparisons to HTML for visualization
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.token_comparison_logger import TokenComparisonLogger
import yaml


def enable_debug_mode(config_path: str = "conf.yaml"):
    """Enable token comparison debug mode in configuration."""
    config_file = Path(config_path)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Enable debug mode
    if 'TOKEN_MANAGEMENT' not in config:
        config['TOKEN_MANAGEMENT'] = {}
    
    if 'debug' not in config['TOKEN_MANAGEMENT']:
        config['TOKEN_MANAGEMENT']['debug'] = {}
    
    config['TOKEN_MANAGEMENT']['debug']['enabled'] = True
    
    # Save updated config
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("✅ Token comparison debug mode ENABLED")
    print("   Comparisons will be saved to: logs/token_comparisons/")
    print("   Remember to disable when done to avoid performance impact!")


def disable_debug_mode(config_path: str = "conf.yaml"):
    """Disable token comparison debug mode in configuration."""
    config_file = Path(config_path)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Disable debug mode
    if 'TOKEN_MANAGEMENT' in config and 'debug' in config['TOKEN_MANAGEMENT']:
        config['TOKEN_MANAGEMENT']['debug']['enabled'] = False
    
    # Save updated config
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("✅ Token comparison debug mode DISABLED")


def list_comparisons(output_dir: str = "logs/token_comparisons"):
    """List all saved token comparisons."""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print("No comparisons found. Directory doesn't exist.")
        return
    
    # List JSON files
    json_path = output_path / "json"
    if json_path.exists():
        json_files = sorted(json_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if json_files:
            print(f"\nFound {len(json_files)} comparison(s):\n")
            print(f"{'Timestamp':<20} {'Node':<25} {'Model':<20} {'Reduction':<15} {'File'}")
            print("-" * 100)
            
            for json_file in json_files:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                timestamp = data['metadata']['timestamp'][:19]  # Trim to seconds
                node = data['metadata']['node_name']
                model = data['metadata']['model_name']
                reduction = f"{data['statistics']['reduction_percentage']:.1f}%"
                
                print(f"{timestamp:<20} {node:<25} {model:<20} {reduction:<15} {json_file.name}")
        else:
            print("No comparisons found.")
    else:
        print("No comparisons found.")


def view_comparison(filename: str, output_dir: str = "logs/token_comparisons", format: str = "markdown"):
    """View a specific comparison."""
    output_path = Path(output_dir)
    
    if format == "markdown":
        file_path = output_path / "markdown" / filename
    else:
        file_path = output_path / "json" / filename
    
    if not file_path.exists():
        # Try to find the file by base name
        base_name = Path(filename).stem
        if format == "markdown":
            file_path = output_path / "markdown" / f"{base_name}.md"
        else:
            file_path = output_path / "json" / f"{base_name}.json"
    
    if file_path.exists():
        with open(file_path, 'r') as f:
            content = f.read()
        print(content)
    else:
        print(f"Comparison file not found: {filename}")


def generate_summary_report(output_dir: str = "logs/token_comparisons"):
    """Generate a summary report of all comparisons."""
    summary_path = Path(output_dir) / "summary" / "trimming_summary.json"
    
    if not summary_path.exists():
        print("No summary data found. Run some comparisons first.")
        return
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    print("\n📊 TOKEN TRIMMING SUMMARY REPORT")
    print("=" * 60)
    print(f"\nTotal Comparisons: {summary['total_comparisons']}")
    print(f"Total Tokens Saved: {summary['total_tokens_saved']:,}")
    print(f"Average Reduction: {summary.get('average_reduction_percentage', 0):.1f}%")
    
    print("\n📈 BY NODE:")
    print("-" * 60)
    print(f"{'Node':<30} {'Comparisons':<15} {'Tokens Saved':<15}")
    print("-" * 60)
    
    for node_name, node_data in summary.get('by_node', {}).items():
        print(f"{node_name:<30} {node_data['comparisons']:<15} {node_data['total_tokens_saved']:,}")
    
    print("\n✨ Use --view <filename> to see specific comparisons")


def convert_to_html(filename: str, output_dir: str = "logs/token_comparisons"):
    """Convert a JSON comparison to HTML format."""
    logger = TokenComparisonLogger(enabled=True, output_dir=output_dir)
    
    json_path = Path(output_dir) / "json" / filename
    if not json_path.exists():
        # Try with just base name
        base_name = Path(filename).stem
        json_path = Path(output_dir) / "json" / f"{base_name}.json"
    
    if json_path.exists():
        html_path = logger.generate_html_report(str(json_path))
        if html_path:
            print(f"✅ HTML report generated: {html_path}")
            print(f"   Open in browser: file://{Path(html_path).absolute()}")
    else:
        print(f"JSON file not found: {filename}")


def clean_old_comparisons(output_dir: str = "logs/token_comparisons", days: int = 7):
    """Clean comparisons older than specified days."""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print("No comparisons to clean.")
        return
    
    from datetime import timedelta
    cutoff_time = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    for subdir in ["json", "markdown", "html"]:
        dir_path = output_path / subdir
        if dir_path.exists():
            for file_path in dir_path.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
    
    print(f"✅ Cleaned {deleted_count} files older than {days} days")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze token trimming comparisons",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enable debug mode
  python scripts/analyze_token_trimming.py --enable
  
  # List all comparisons
  python scripts/analyze_token_trimming.py --list
  
  # View a specific comparison
  python scripts/analyze_token_trimming.py --view planner_deepseek-chat_20240115_143022.md
  
  # Generate summary report
  python scripts/analyze_token_trimming.py --summary
  
  # Convert to HTML
  python scripts/analyze_token_trimming.py --html planner_deepseek-chat_20240115_143022.json
  
  # Clean old files
  python scripts/analyze_token_trimming.py --clean 7
        """
    )
    
    parser.add_argument('--enable', action='store_true', help='Enable token comparison debug mode')
    parser.add_argument('--disable', action='store_true', help='Disable token comparison debug mode')
    parser.add_argument('--list', action='store_true', help='List all saved comparisons')
    parser.add_argument('--view', metavar='FILENAME', help='View a specific comparison')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', 
                       help='Format for viewing (default: markdown)')
    parser.add_argument('--summary', action='store_true', help='Generate summary report')
    parser.add_argument('--html', metavar='FILENAME', help='Convert JSON comparison to HTML')
    parser.add_argument('--clean', type=int, metavar='DAYS', 
                       help='Clean comparisons older than DAYS')
    parser.add_argument('--output-dir', default='logs/token_comparisons', 
                       help='Output directory (default: logs/token_comparisons)')
    
    args = parser.parse_args()
    
    if args.enable:
        enable_debug_mode()
    elif args.disable:
        disable_debug_mode()
    elif args.list:
        list_comparisons(args.output_dir)
    elif args.view:
        view_comparison(args.view, args.output_dir, args.format)
    elif args.summary:
        generate_summary_report(args.output_dir)
    elif args.html:
        convert_to_html(args.html, args.output_dir)
    elif args.clean:
        clean_old_comparisons(args.output_dir, args.clean)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()