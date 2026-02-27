from __future__ import annotations
import os
import logging

def setup_logger(name="factor_lab"):
    level = os.getenv("FACTOR_LAB_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    return logging.getLogger(name)
