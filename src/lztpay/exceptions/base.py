from typing import Any, Dict, Optional


class LZTPayError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIError(LZTPayError):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, {"status_code": status_code, "response": response})
        self.status_code = status_code
        self.response = response


class AuthError(LZTPayError):
    pass


class RateLimitError(APIError):
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            "Rate limit exceeded",
            status_code=429,
            response={"retry_after": retry_after},
        )
        self.retry_after = retry_after


class PaymentNotFoundError(LZTPayError):
    pass


class ValidationError(LZTPayError):
    pass


class NetworkError(LZTPayError):
    pass
