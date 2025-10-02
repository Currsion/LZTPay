from functools import wraps
from typing import Any, Callable, Dict

from pydantic import BaseModel, ValidationError as PydanticValidationError

from ..exceptions import ValidationError
from ..logger import get_logger

logger = get_logger()


def validate_params(model: type[BaseModel]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                validated = model(**kwargs)
                new_kwargs = validated.model_dump()
                return func(*args, **new_kwargs)
            except PydanticValidationError as e:
                errors = e.errors()
                logger.error(
                    "validation failed",
                    func=func.__name__,
                    errors=[{"field": err["loc"][0], "msg": err["msg"]} for err in errors],
                )
                raise ValidationError(
                    f"Invalid parameters for {func.__name__}",
                    details={"errors": errors},
                )

        return wrapper

    return decorator
