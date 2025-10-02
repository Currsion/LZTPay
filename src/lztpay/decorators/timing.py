import asyncio
import sys
import time
from functools import wraps
from typing import Any, Callable

from lztpay.logger import get_logger

logger = get_logger()


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(
                "execution completed",
                func=func.__name__,
                elapsed_ms=round(elapsed * 1000, 2),
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(
                "execution failed",
                func=func.__name__,
                elapsed_ms=round(elapsed * 1000, 2),
                error=str(e),
            )
            raise e.with_traceback(None)

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(
                "execution completed",
                func=func.__name__,
                elapsed_ms=round(elapsed * 1000, 2),
            )
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(
                "execution failed",
                func=func.__name__,
                elapsed_ms=round(elapsed * 1000, 2),
                error=str(e),
            )
            raise e.with_traceback(None)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
