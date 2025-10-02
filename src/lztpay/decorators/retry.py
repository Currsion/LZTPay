import asyncio
import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type

from ..exceptions import NetworkError, RateLimitError
from ..logger import get_logger

logger = get_logger()


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (NetworkError, RateLimitError),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            "all retry attempts failed",
                            func=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )
                        raise

                    logger.warn(
                        "retrying after error",
                        func=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=current_delay,
                        error=str(e),
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            if last_exception:
                raise last_exception

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            "all retry attempts failed",
                            func=func.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )
                        raise

                    logger.warn(
                        "retrying after error",
                        func=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=current_delay,
                        error=str(e),
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

            if last_exception:
                raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
