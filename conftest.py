import sys
import os

# Expose the src/ package to pytest and all test modules automatically.
# This file is discovered and executed by pytest before any test collection,
# making sys.path manipulation in individual test files unnecessary.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
