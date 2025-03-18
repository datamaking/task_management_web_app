import time
import psutil
from memory_profiler import memory_usage
import functools
import logging

logger = logging.getLogger(__name__)

def profile_memory(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024 * 1024)  # in MB
        start_time = time.time()

        # Measure memory usage during the function call
        mem_usage, result = memory_usage((func, args, kwargs), retval=True, interval=0.1, max_iterations=1)

        end_time = time.time()
        mem_after = process.memory_info().rss / (1024 * 1024)  # in MB

        logger.info("Function %s took %.2f seconds", func.__name__, end_time - start_time)
        logger.info("Memory usage (psutil): before: %.2f MB, after: %.2f MB", mem_before, mem_after)
        logger.info("Memory usage (memory_profiler) - peak: %.2f MB", max(mem_usage))
        return result
    return wrapper
