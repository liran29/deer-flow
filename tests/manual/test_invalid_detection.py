#!/usr/bin/env python3
"""测试INVALID内容检测逻辑"""

def test_invalid_detection():
    # 模拟llm_summarize_search_result的逻辑
    test_cases = [
        "[INVALID] The content provided is a generic Reddit navigation menu...",
        "Valid content about Walmart Christmas decorations",
        "Some content with [INVALID] in the middle",
        "[INVALID]No space after marker",
        "  [INVALID] With leading spaces",
    ]
    
    for i, response_text in enumerate(test_cases):
        response_text = response_text.strip()
        
        # 按照prompt设计检查LLM是否标记内容为无效
        if response_text.startswith("[INVALID]"):
            reason = response_text[9:].strip()
            print(f"Case {i+1}: is_valid=False, reason='{reason[:50]}...'")
        elif "[INVALID]" in response_text:
            print(f"Case {i+1}: is_valid=False, reason='Invalid format in response'")
        else:
            print(f"Case {i+1}: is_valid=True, summary='{response_text[:50]}...'")

if __name__ == "__main__":
    test_invalid_detection()