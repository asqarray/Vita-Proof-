import os
import ctypes
import logging

logger = logging.getLogger(__name__)

CORE_LIB_PATHS = [
    "/app/vitaproof_core.so",
    "./vitaproof_core.so",
    "./programs/vitaproof_settlement.so"
]

core_lib = None
core_loaded = False

for path in CORE_LIB_PATHS:
    if os.path.exists(path):
        try:
            core_lib = ctypes.CDLL(path)
            core_loaded = True
            logger.info(f"Loaded core library from {path}")
            break
        except (OSError, Exception) as e:
            logger.warning(f"File exists at {path} but cannot be loaded via ctypes (SBF/eBPF binary): {e}")

if not core_loaded:
    logger.info("Operating in pure-Python settlement fallback mode.")