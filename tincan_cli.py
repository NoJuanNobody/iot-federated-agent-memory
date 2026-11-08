#!/usr/bin/env python3
import os
import sys

# Ensure package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iot_federated_agent_memory.tincan_cli import main

if __name__ == "__main__":
    sys.exit(main())
