#!/usr/bin/env python3
import sys
import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()

    test_dir = sys.argv[1] if len(sys.argv) > 1 else "tests"

    suite = loader.discover(test_dir)
    runner = unittest.TextTestRunner()
    runner.run(suite)