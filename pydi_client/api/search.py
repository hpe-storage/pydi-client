# Copyright Hewlett Packard Enterprise Development LP

from http import HTTPStatus
from typing import Any, Dict, Optional, Union

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.sessions.session import Session
from pydi_client.errors import SimilaritySearchFailureException
from pydi_client.api.utils import execute_with_retry, build_response
from pydi_client.data.pipeline import V1SimilaritySearchResponse
from pydi_client.logger import get_logger  # Importing the logger utility

# Initialize logger for this module
logger = get_logger()

_REDACTED = "***"


def _redact_request(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    body = dict(kwargs.get("json") or {})
    if "credentials" in body:
        body["credentials"] = {**body["credentials"], "secretKey": _REDACTED}
    if "fileCredentials" in body:
        body["fileCredentials"] = {**body["fileCredentials"], "password": _REDACTED}
    return {**kwargs, "json": body}


class SimilaritySearchAPI:
    """
    Class to perform similarity search using the PyDI API.
    """

    def __init__(self, session: Union[AuthenticatedSession, Session]):
        self._session = session
        logger.info(
            "SimilaritySearchAPI initialized with session: %s", type(session).__name__
        )

    def search(
        self,
        *,
        collection_name: str,
        query: str,
        top_k: int,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        file_username: Optional[str] = None,
        file_password: Optional[str] = None,
        search_parameters: Union[Dict[str, Any]] = None,
    ) -> V1SimilaritySearchResponse:
        """
        Perform a similarity search in the specified collection.

        Collections with S3 bucket sources need ``access_key`` and ``secret_key``.
        Collections with a filesystem source need ``file_username`` and
        ``file_password`` of a file user; results are limited to files that user
        can open. Both pairs may be supplied; the server uses the one that matches
        the collection's source.

        Args:
            collection_name (str): The name of the collection to search in.
            query (str): The query string to search for.
            top_k (int): The number of top results to return.
            access_key (Optional[str]): The access key for S3 credentials.
            secret_key (Optional[str]): The secret key for S3 credentials.
            file_username (Optional[str]): File user name for filesystem-sourced collections.
            file_password (Optional[str]): File user password for filesystem-sourced collections.
            search_parameters (Dict[str, Any]): Additional search parameters.

        Returns:
            V1SimilaritySearchResponse: The search results.

            Sample response: List of similar data chunks
                {
                "success": True,
                "message": "Similarity search completed successfully.",
                "results": [
                    {
                        "score": 0,
                        "dataChunk": "string",
                        "chunkMetadata": {
                            "sourceType": "S3",
                            "objectKey": "string",
                            "startCharIdx" : 1,
                            "endCharIdx" : 2,
                            "bucketName": "string",
                            "pageLabel": "string",
                            "versionId": "string",
                        }
                    }
                ]
                }

        Raises:
            ValueError: If a credential pair is incomplete or no credentials are given.
            FileUserAuthenticationError: If the file user credentials were rejected.
            SimilaritySearchFailureException: If the search failed for any other reason.
        """
        has_s3_credentials = access_key is not None or secret_key is not None
        has_file_credentials = file_username is not None or file_password is not None
        if has_s3_credentials and (access_key is None or secret_key is None):
            raise ValueError("access_key and secret_key must be provided together.")
        if has_file_credentials and (file_username is None or file_password is None):
            raise ValueError(
                "file_username and file_password must be provided together."
            )
        if not has_s3_credentials and not has_file_credentials:
            raise ValueError(
                "Provide access_key and secret_key for collections with bucket sources, "
                "or file_username and file_password for collections with a filesystem source."
            )

        logger.info(
            "Performing similarity search in collection: %s with query: %s and top_k: %d",
            collection_name,
            query,
            top_k,
        )

        kwargs: Dict[str, Any] = {"method": "POST", "url": "/api/v1/similaritySearch"}

        body: Dict[str, Any] = {
            "collectionName": collection_name,
            "query": query,
            "topK": top_k,
            "searchParams": search_parameters,
        }
        if has_s3_credentials:
            body["credentials"] = {"accessKey": access_key, "secretKey": secret_key}
        if has_file_credentials:
            body["fileCredentials"] = {
                "username": file_username,
                "password": file_password,
            }

        kwargs["json"] = body

        logger.debug(
            "Request payload for similarity search: %s", _redact_request(kwargs)
        )

        # The search endpoint does not use the session token, so a 401 here is never
        # fixed by refreshing the session.
        response = execute_with_retry(
            session=self._session,
            request_func=self._session.get_httpx_client().request,
            refresh_on_unauthorized=False,
            **kwargs,
        )

        logger.debug("Similarity search response status code: %s", response.status_code)

        if response.status_code == HTTPStatus.OK:
            logger.info(
                "Similarity search completed successfully for collection: %s",
                collection_name,
            )
            # validate response
            resp = build_response(
                response=response, response_cls=V1SimilaritySearchResponse
            )
            return resp.model_dump().get("results", [])

        else:
            logger.error(
                "Similarity search failed for collection: %s with status code: %s and response: %s",
                collection_name,
                response.status_code,
                response.text,
            )
            raise SimilaritySearchFailureException(
                f"Similarity search failed with status code {response.status_code}: {response.text}"
            )
