# Copyright Hewlett Packard Enterprise Development LP

import httpx
import json
from httpx import Response
from typing import Any, Dict, Callable

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.api.auth import AuthAPI
from pydi_client.errors import (
    FileUserAuthenticationError,
    HTTPUnauthorizedException,
    PipelineValidationError,
    UnexpectedResponse,
    UnexpectedStatus,
    parse_server_validation_errors,
)
from pydi_client.data.collection_manager import ListCollection, ListPipelines

from pydi_client.logger import get_logger  # Importing the logger utility

# Initialize logger for this module
logger = get_logger()

# Error text the API gateway returns for rejected file user credentials.
FILE_USER_AUTH_ERROR = "Invalid file user credentials"


def is_file_user_auth_failure(response: Response) -> bool:
    """Return True if the response rejects file user credentials, not the session."""
    if response.status_code != 401:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return isinstance(payload, dict) and payload.get("error") == FILE_USER_AUTH_ERROR


def execute_with_retry(
    session,
    request_func: Callable,
    *,
    refresh_on_unauthorized: bool = True,
    **kwargs: Dict[str, Any],
) -> Response:
    """
    Executes an HTTP request with retry logic for unauthorized errors.

    Args:
        session: The session object (AuthenticatedSession or Session).
        request_func: The function to execute the HTTP request.
        refresh_on_unauthorized: If False, a 401/403 response is returned to the
            caller instead of refreshing the session and retrying.
        kwargs: Arguments to pass to the request function.

    Returns:

    Raises:
        FileUserAuthenticationError: If the server rejected the file user credentials.
            The session is not refreshed and the request is not retried.
        HTTPUnauthorizedException: If the request fails even after retrying.
    """
    resp = request_func(**kwargs)
    if resp is not None:
        logger.debug(
            "Response Status Code: %s, Response Text: %s",
            resp.status_code,
            resp.text,
        )

        if resp.status_code == 401 or resp.status_code == 403:
            # Re-sending rejected file user credentials cannot succeed and would
            # count twice toward the server's credential lockout.
            if is_file_user_auth_failure(resp):
                logger.error(
                    "File user credentials were rejected; not refreshing the session or retrying."
                )
                raise FileUserAuthenticationError()

            if not refresh_on_unauthorized:
                return resp

            logger.warning(
                "Unauthorized access detected. Attempting to refresh session."
            )

            if isinstance(session, AuthenticatedSession):
                logger.info("Refreshing session for authenticated user.")
                AuthAPI.refresh(session=session)  # Refresh the session
                request_func = (
                    session.get_httpx_client().request
                )  # refresh the function
                return request_func(**kwargs)
            else:
                raise HTTPUnauthorizedException(
                    "Unauthorized access. Session is not authenticated."
                )

    return resp


def raise_for_admin_error(
    response: httpx.Response, error_type: type[PipelineValidationError]
) -> None:
    """Normalize non-authentication 4xx responses from admin write operations."""
    if 400 <= response.status_code < 500 and response.status_code not in (401, 403):
        raise error_type(
            errors=parse_server_validation_errors(response.content),
            source="server",
            status_code=response.status_code,
            raw_response=response.content,
        )


def build_response(*, response: httpx.Response, response_cls: Any) -> Any:
    if httpx.codes.OK <= response.status_code <= httpx.codes.CREATED:

        response_200 = None

        if not response.content or response.content.strip() == b"":
            return response_200

        try:
            _response_200 = response.json()
            if response_cls in (ListCollection, ListPipelines):
                response_200 = response_cls(root=_response_200)
            else:
                response_200 = response_cls(**_response_200)
        except TypeError as e:
            raise UnexpectedResponse(response.status_code, response.content) from e
        except json.JSONDecodeError as e:
            raise UnexpectedResponse(response.status_code, response.content) from e
        return response_200

    if response.status_code == 401:
        raise HTTPUnauthorizedException(
            "Unauthorized access. Please check your credentials or refresh session"
        )
    else:
        raise UnexpectedStatus(response.status_code, response.content)
