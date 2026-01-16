#!/usr/bin/env python
"""Test script for mechpy Rust extension"""

import mechpy

def test_basic_import():
    """Test that mechpy can be imported and has expected modules"""
    assert hasattr(mechpy, 'sensor'), "mechpy should have sensor module"
    print("✓ mechpy imported successfully with sensor module")
    print("\nAll tests passed! 🎉")

if __name__ == "__main__":
    test_basic_import()
