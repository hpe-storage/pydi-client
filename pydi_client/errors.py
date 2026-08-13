# Copyright Hewlett Packard Enterprise Development LP

from functools import wraps
from inspect import Parameter, signature
from typing import Any, Callable, Dict, List, Literal, Optional, ParamSpec, TypeVar


P = ParamSpec("P")
T = TypeVar("T")


class PipelineValidationError(ValueError):
    """Exception raised when pipeline creation input is invalid."""

    def __init__(
        self,
        *,
        errors: List[Dict[str, Any]],
        source: Literal["client", "server"],
        status_code: Optional[int] = None,
        raw_response: Optional[bytes] = None,
    ):
        self.errors = errors
        self.source = source
        self.status_code = status_code
        self.raw_response = raw_response

        super().__init__(self._message())

    def _message(self) -> str:
        details = []
        for error in self.errors:
            rendered_error = self._format_error(error)
            if rendered_error:
                details.append(rendered_error)

        prefix = f"Pipeline validation failed ({self.source})"
        return (
            f"{prefix}: {'; '.join(details)}"
            if details
            else f"{prefix}: no error details"
        )

    @staticmethod
    def _format_error(error: Dict[str, Any]) -> str:
        message = error.get("msg")
        if not isinstance(message, str):
            return ""

        location = error.get("loc")
        if isinstance(location, (list, tuple)) and location:
            return f"{'.'.join(str(part) for part in location)}: {message}"

        status = error.get("status")
        if isinstance(status, str) and status:
            return f"{status}: {message}"

        return message


def normalize_pipeline_argument_errors(
    function: Callable[P, T],
) -> Callable[P, T]:
    """Convert pipeline method argument-binding failures to validation errors."""
    function_signature = signature(function)

    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            function_signature.bind(*args, **kwargs)
        except TypeError as error:
            try:
                bound_arguments = function_signature.bind_partial(*args, **kwargs)
                missing_arguments = [
                    parameter.name
                    for parameter in function_signature.parameters.values()
                    if parameter.name != "self"
                    and parameter.default is Parameter.empty
                    and parameter.name not in bound_arguments.arguments
                ]
            except TypeError:
                missing_arguments = []

            errors = [
                {"type": "missing", "loc": [name], "msg": "Field required"}
                for name in missing_arguments
            ] or [{"type": "argument_binding_error", "loc": [], "msg": str(error)}]

            raise PipelineValidationError(errors=errors, source="client") from error

        return function(*args, **kwargs)

    return wrapper


class NotImplementedException(Exception):
    """Exception raised for methods that are not implemented."""

    def __init__(self, message="This method is not implemented."):
        super().__init__(message)


class HTTPUnauthorizedException(Exception):
    """Exception raised for HTTP 401 Unauthorized errors."""

    def __init__(
        self,
        message="HTTP 401 Unauthorized: Access is denied due to invalid credentials.",
    ):
        super().__init__(message)


class SimilaritySearchFailureException(Exception):
    """Exception raised when a similarity search operation fails."""

    def __init__(self, message="Similarity search operation failed."):
        super().__init__(message)


class UnexpectedStatus(Exception):
    """Raised by api functions when the response status an unexpected status"""

    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self.content = content

        super().__init__(
            f"Unexpected status code: {status_code}\n\nResponse content:\n{content.decode(errors='ignore')}"
        )


class UnexpectedResponse(Exception):
    """Exception raised when an API response is not as expected."""

    def __init__(self, status_code: int, response: bytes):
        self.status_code = status_code
        self.response = response

        super().__init__(
            f"Unexpected response: {status_code}\n\nResponse content:\n{response.decode(errors='ignore')}"
        )
