# utils.py
import time
import logging
import functools
import sys

# Logger dedicado
logger = logging.getLogger("timing")
if not logger.handlers:  # evita handlers duplicados en reruns de Streamlit
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # que no burbujee al root

def log_timing(func):
    """Mide el tiempo de ejecución y loguea en consola."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.time() - start
            logger.info(f"{func.__name__} tardó {elapsed:.3f}s")
    return wrapper
