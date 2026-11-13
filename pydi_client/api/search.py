# Copyright Hewlett Packard Enterprise Development LP

from http import HTTPStatus
from typing import Any, Dict, Optional, Union, List

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.sessions.session import Session
from pydi_client.errors import SimilaritySearchFailureException
from pydi_client.api.utils import execute_with_retry, build_response
from pydi_client.data.pipeline import V1SimilaritySearchResponse
from pydi_client.logger import get_logger  # Importing the logger utility

# Initialize logger for this module
logger = get_logger()


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

        Pass S3 credentials for a bucket collection, or file user credentials
        for a filesystem collection. Exactly one of the two must be given.

        Args:
            collection_name (str): The name of the collection to search in.
            query (str): The query string to search for.
            top_k (int): The number of top results to return.
            access_key (Optional[str]): The access key for S3 credentials.
            secret_key (Optional[str]): The secret key for S3 credentials.
            file_username (Optional[str]): File user name for a filesystem collection.
            file_password (Optional[str]): File user password for a filesystem collection.
            search_parameters (Dict[str, Any]): Additional search parameters.

        Raises:
            ValueError: If neither or both credential sets are given, or a set is incomplete.

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
                            "objectKey": "string",
                            "startCharIndex" : 1,
                            "endCharIndex" : 2,
                            "bucketName": "string",
                            "pageLabel": "string",
                            "versionId": "string",
                        }
                    }
                ]
                }

            A filesystem collection returns chunkMetadata with
            "sourceType": "FILE" and "filePath" instead of the S3 fields.
        """
        s3_given = access_key is not None or secret_key is not None
        file_given = file_username is not None or file_password is not None
        if s3_given == file_given:
            raise ValueError(
                "Provide either access_key/secret_key (bucket collection) "
                "or file_username/file_password (filesystem collection), not both"
            )
        if s3_given and not (access_key and secret_key):
            raise ValueError("Both access_key and secret_key are required")
        if file_given and not (file_username and file_password):
            raise ValueError("Both file_username and file_password are required")

        logger.info(
            "Performing similarity search in collection: %s with query: %s and top_k: %d",
            collection_name,
            query,
            top_k,
        )

        kwargs: Dict[str, Any] = {"method": "POST", "url": "/api/v1/similaritySearch"}

        body = {
            "collectionName": collection_name,
            "query": query,
            "topK": top_k,
            "searchParams": search_parameters,
        }
        if s3_given:
            body["credentials"] = {"accessKey": access_key, "secretKey": secret_key}
        else:
            body["fileCredentials"] = {
                "username": file_username,
                "password": file_password,
            }

        kwargs["json"] = body

        logger.debug(
            "Request payload for similarity search: %s",
            {
                k: v
                for k, v in body.items()
                if k not in ("credentials", "fileCredentials")
            },
        )

        response = execute_with_retry(
            session=self._session,
            request_func=self._session.get_httpx_client().request,
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
