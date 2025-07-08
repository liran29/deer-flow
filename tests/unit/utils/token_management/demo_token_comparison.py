"""
Demo script showing how to use the token comparison logging feature.

This demonstrates:
1. Enabling debug mode
2. Running token trimming with comparisons
3. Viewing the results
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.utils.token_manager import TokenManager
from src.utils.token_comparison_logger import TokenComparisonLogger


def create_sample_conversation():
    """Create a sample conversation that will be trimmed."""
    messages = [
        SystemMessage(content="You are a helpful research assistant."),
        HumanMessage(content="I need help researching quantum computing."),
        AIMessage(content="I'd be happy to help you research quantum computing. Let me start by providing an overview..."),
        HumanMessage(content="Can you explain qubits?"),
        AIMessage(content="Qubits, or quantum bits, are the fundamental units of quantum information. Unlike classical bits that can be either 0 or 1, qubits can exist in a superposition of both states simultaneously. This property, along with entanglement, gives quantum computers their computational power..."),
        HumanMessage(content="What about quantum entanglement?"),
        AIMessage(content="Quantum entanglement is a phenomenon where two or more quantum particles become correlated in such a way that the quantum state of each particle cannot be described independently. When particles are entangled, measuring the state of one particle instantly affects the state of the other, regardless of the distance between them. Einstein famously called this 'spooky action at a distance'..."),
        HumanMessage(content="How does this apply to computing?"),
        AIMessage(content="In quantum computing, entanglement is crucial for several reasons: 1) It enables quantum parallelism, allowing quantum computers to process multiple possibilities simultaneously. 2) It's essential for quantum algorithms like Shor's algorithm for factoring large numbers. 3) It enables quantum error correction schemes..."),
        HumanMessage(content="What are the main challenges?"),
        AIMessage(content="The main challenges in quantum computing include: 1) Decoherence - qubits are extremely sensitive to environmental interference. 2) Error rates - quantum operations are prone to errors. 3) Scalability - building systems with many stable qubits is difficult. 4) Temperature requirements - most quantum computers need to operate near absolute zero..."),
    ]
    
    # Add more messages to trigger trimming
    for i in range(5):
        messages.extend([
            HumanMessage(content=f"Additional question {i+1} about quantum computing applications in cryptography, medicine, and materials science."),
            AIMessage(content=f"Detailed response {i+1}: Quantum computing has numerous applications across various fields. In cryptography, quantum computers threaten current encryption methods but also enable quantum key distribution. In medicine, they can accelerate drug discovery by simulating molecular interactions. In materials science, they can help design new materials with specific properties...")
        ])
    
    return messages


def demo_basic_comparison():
    """Demonstrate basic token comparison logging."""
    print("=== Token Comparison Demo ===\n")
    
    # Create a token manager with debug enabled
    # Note: You would normally enable this in conf.yaml
    token_manager = TokenManager()
    token_manager.comparison_logger = TokenComparisonLogger(
        enabled=True,
        output_dir="logs/token_comparisons_demo",
        max_content_preview=200,
        save_full_content=True
    )
    
    # Create sample messages
    messages = create_sample_conversation()
    print(f"Created {len(messages)} sample messages")
    
    # Test different nodes with different strategies
    test_cases = [
        ("planner", "deepseek-chat", {"max_tokens": 1000, "strategy": "last"}),
        ("researcher", "gemini-2.0-flash", {"max_tokens": 2000, "strategy": "last"}),
        ("reporter", "deepseek-chat", {"max_tokens": 500, "strategy": "first"}),
    ]
    
    for node_name, model_name, strategy in test_cases:
        print(f"\n--- Testing {node_name} with {model_name} ---")
        
        # Override strategy for testing
        original_strategy = token_manager.get_trimming_strategy(node_name)
        token_manager.token_management["trimming_strategies"][node_name] = strategy
        
        # Trim messages
        trimmed = token_manager.trim_messages_for_node(
            messages=messages,
            model_name=model_name,
            node_name=node_name
        )
        
        print(f"Original: {len(messages)} messages")
        print(f"Trimmed: {len(trimmed)} messages")
        print(f"Removed: {len(messages) - len(trimmed)} messages")
        
        # Restore original strategy
        if original_strategy:
            token_manager.token_management["trimming_strategies"][node_name] = original_strategy
    
    print("\n✅ Comparisons saved to: logs/token_comparisons_demo/")
    print("   View with: python scripts/analyze_token_trimming.py --list --output-dir logs/token_comparisons_demo")


def demo_detailed_analysis():
    """Demonstrate detailed analysis of trimming patterns."""
    print("\n=== Detailed Trimming Analysis ===\n")
    
    # Create logger for analysis
    logger = TokenComparisonLogger(
        enabled=True,
        output_dir="logs/token_comparisons_demo",
        max_content_preview=300,
        save_full_content=True
    )
    
    # Test edge cases
    edge_cases = [
        {
            "name": "All System Messages",
            "messages": [SystemMessage(content=f"System instruction {i}") for i in range(10)],
            "strategy": {"strategy": "last", "include_system": False}
        },
        {
            "name": "Alternating Human/AI",
            "messages": [
                HumanMessage(content=f"Question {i//2}") if i % 2 == 0 
                else AIMessage(content=f"Answer {i//2}")
                for i in range(20)
            ],
            "strategy": {"strategy": "first", "max_tokens": 500}
        },
        {
            "name": "Long Single Message",
            "messages": [
                HumanMessage(content="Short question"),
                AIMessage(content="A" * 10000)  # Very long response
            ],
            "strategy": {"strategy": "last", "max_tokens": 100}
        }
    ]
    
    for case in edge_cases:
        print(f"\nTesting: {case['name']}")
        
        # Simulate trimming (simplified for demo)
        trimmed = case["messages"][:len(case["messages"])//2]
        
        comparison_path = logger.log_comparison(
            original_messages=case["messages"],
            trimmed_messages=trimmed,
            node_name=case["name"].lower().replace(" ", "_"),
            model_name="test-model",
            max_tokens=case["strategy"].get("max_tokens", 1000),
            strategy=case["strategy"]
        )
        
        if comparison_path:
            print(f"  Saved to: {comparison_path}")


def demo_html_visualization():
    """Demonstrate HTML report generation."""
    print("\n=== HTML Visualization Demo ===\n")
    
    logger = TokenComparisonLogger(
        enabled=True,
        output_dir="logs/token_comparisons_demo"
    )
    
    # Create a comparison with rich content
    messages = [
        SystemMessage(content="You are an expert in machine learning."),
        HumanMessage(content="Explain neural networks with examples."),
        AIMessage(content="""
Neural networks are computational models inspired by the human brain. They consist of:

1. **Input Layer**: Receives the initial data
2. **Hidden Layers**: Process the information
3. **Output Layer**: Produces the final result

Example: Image Recognition
- Input: Pixel values of an image
- Hidden layers: Extract features (edges, shapes, objects)
- Output: Classification (cat, dog, car, etc.)

```python
# Simple neural network example
import numpy as np

class NeuralNetwork:
    def __init__(self, layers):
        self.layers = layers
        self.weights = self._initialize_weights()
    
    def forward(self, x):
        for w in self.weights:
            x = self.sigmoid(np.dot(x, w))
        return x
```
        """),
        HumanMessage(content="What about deep learning?"),
        AIMessage(content="Deep learning uses neural networks with many hidden layers...")
    ]
    
    # Log comparison
    comparison_path = logger.log_comparison(
        original_messages=messages * 3,  # Repeat to simulate longer conversation
        trimmed_messages=messages[:3],
        node_name="ml_expert",
        model_name="gpt-4",
        max_tokens=1000,
        strategy={"strategy": "last"},
        token_counts={"original": 2500, "trimmed": 800}
    )
    
    if comparison_path:
        # Generate HTML
        json_file = comparison_path.replace("/markdown/", "/json/").replace(".md", ".json")
        html_path = logger.generate_html_report(json_file)
        
        if html_path:
            print(f"HTML report generated: {html_path}")
            print(f"Open in browser: file://{Path(html_path).absolute()}")


def main():
    """Run all demos."""
    print("🔍 Token Comparison Logger Demo\n")
    
    # Run demos
    demo_basic_comparison()
    demo_detailed_analysis()
    demo_html_visualization()
    
    print("\n\n📊 Summary Commands:")
    print("  List all comparisons:")
    print("    python scripts/analyze_token_trimming.py --list --output-dir logs/token_comparisons_demo")
    print("\n  View specific comparison:")
    print("    python scripts/analyze_token_trimming.py --view <filename> --output-dir logs/token_comparisons_demo")
    print("\n  Generate summary:")
    print("    python scripts/analyze_token_trimming.py --summary --output-dir logs/token_comparisons_demo")
    print("\n  Clean up demo files:")
    print("    rm -rf logs/token_comparisons_demo")


if __name__ == "__main__":
    main()