import functools
import time


# Retry decorator
def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: int = 2,
    exceptions: tuple = (Exception,),
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay: float = delay
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return wrapper

    return decorator
