#!/usr/bin/env python3
"""Simple test for logging configuration."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

print("Testing imports...")

try:
    import structlog
    print(f"✓ structlog version: {structlog.__version__}")
    structlog_available = True
except ImportError as e:
    print(f"✗ structlog not available: {e}")
    structlog_available = False

try:
    from core.observability.logging import get_logger, new_correlation_id
    logger = get_logger("test")
    print(f"✓ Observability logger type: {type(logger)}")
    observability_available = True
except ImportError as e:
    print(f"✗ Observability not available: {e}")
    observability_available = False

try:
    from core.agents.agent_sdk.auth import STRUCTURED_LOGGING
    print(f"✓ STRUCTURED_LOGGING flag: {STRUCTURED_LOGGING}")
except ImportError as e:
    print(f"✗ Auth module not available: {e}")

# Test logging
if observability_available:
    print("\nTesting structured logging...")
    try:
        logger.info("Basic message")
        print("✓ Basic logging works")
    except Exception as e:
        print(f"✗ Basic logging failed: {e}")
    
    try:
        logger.info("Message with params", param1="value1", param2="value2")
        print("✓ Structured logging works")
    except Exception as e:
        print(f"✗ Structured logging failed: {e}")

print("\nDone!")