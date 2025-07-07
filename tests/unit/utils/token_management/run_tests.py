#!/usr/bin/env python3
"""
Test runner for token management tests.

Usage:
    python run_tests.py          # Run all tests
    python run_tests.py --demo   # Run demo only
    python run_tests.py --tests  # Run pytest only
"""

import sys
import os
import subprocess
import argparse

def run_demo():
    """Run the token management demo"""
    print("🦌 Running Token Management Demo...")
    print("=" * 50)
    
    demo_script = os.path.join(os.path.dirname(__file__), "demo_token_management.py")
    try:
        subprocess.run([sys.executable, demo_script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Demo failed with exit code {e.returncode}")
        return False


def run_tests():
    """Run the pytest test suite"""
    print("\n🧪 Running Token Management Tests...")
    print("=" * 50)
    
    test_script = os.path.join(os.path.dirname(__file__), "test_token_management.py")
    try:
        subprocess.run([sys.executable, "-m", "pytest", test_script, "-v"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code {e.returncode}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run token management tests")
    parser.add_argument("--demo", action="store_true", help="Run demo only")
    parser.add_argument("--tests", action="store_true", help="Run tests only")
    
    args = parser.parse_args()
    
    success = True
    
    if args.demo:
        success = run_demo()
    elif args.tests:
        success = run_tests()
    else:
        # Run both by default
        success = run_demo() and run_tests()
    
    if success:
        print("\n✅ All token management components working correctly!")
    else:
        print("\n❌ Some components failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()