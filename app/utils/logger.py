import logging
import functools
import time
from typing import Callable
from contextlib import contextmanager

class LoggerConfig:
    # TODO: add args and retuns in docstring
    def __init__(self):
        # Configure base logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | line: %(lineno)d | %(message)s"
        )
        self.logger = logging.getLogger('resumate')

    def get_logger(self, name: str = None) -> logging.Logger:
        """Get logger instance with optional name"""
        return logging.getLogger(f'resumate.{name}' if name else 'resumate')

    @contextmanager
    def operation_logger(self, operation: str):
        """Context manager for timing operations"""
        start = time.time()
        self.logger.info(f"Starting {operation}")
        try:
            yield
            duration = time.time() - start
            self.logger.info(f"Completed {operation} in {duration:.2f}s")
        except Exception as e:
            self.logger.error(f"Failed {operation}: {str(e)}")
            raise

    def log_execution(self, func: Callable) -> Callable:
        """Decorator for logging function execution"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = self.get_logger(func.__module__)
            logger.debug(f"Executing {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper

