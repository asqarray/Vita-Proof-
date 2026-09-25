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
            logger.info(f"Successfully loaded core library from {path}")
            break
        except Exception as e:
            logger.warning(f"File exists at {path} but failed to load via ctypes: {e}")

if not core_loaded:
    logger.warning("Core library not loaded. Daemon operating in pure-Python fallback mode.")