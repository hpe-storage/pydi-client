# Copyright Hewlett Packard Enterprise Development LP

from typing import Any, Dict, List, Union, Type

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.sessions.session import Session

from pydi_client.data.schema import (
    V1SchemasResponse,
    V1ListSchemasResponse,
    V1CreateSchemaRequest,
    V1CreateSchemaResponse,
    SchemaItem,
    V1DeleteSchemaResponse,
)

from pydi_client.api.utils import execute_with_retry, build_response
from pydi_client.logger import get_logger  # Importing the logger utility
import httpx
from pydantic import BaseModel
from typing import Optional as _Optional

# Initialize logger for this module
logger = get_logger()


class _ServerStatusResponse(BaseModel):
    """Internal model matching the server's raw status response shape."""
    status: _Optional[str] = None


class MethodFactory:
    BASE_URL = "/api/v1/schemas"

    def create_schema(self):
        return self._build("post", f"{self.BASE_URL}")

    def get_schema(self, name):
        return self._build("get", f"{self.BASE_URL}/{name}")

    def get_schemas(self):
        return self._build("get", f"{self.BASE_URL}")

    def _build(self, method, endpoint):
        return {"method": method, "url": endpoint}
    
    def delete_schema(self, name):
        return self._build("delete", f"{self.BASE_URL}/{name}")


class DataModelFactory:

    @staticmethod
    def create_schema() -> Type[V1CreateSchemaResponse]:
        return V1CreateSchemaResponse

    @staticmethod
    def get_schema() -> Type[V1SchemasResponse]:
        return V1SchemasResponse

    @staticmethod
    def get_schemas() -> Type[V1ListSchemasResponse]:
        return V1ListSchemasResponse
    
    @staticmethod
    def delete_schema() -> Type[V1DeleteSchemaResponse]:
        return V1DeleteSchemaResponse


class SchemaAPI:
    """
    A client API for interacting with schema objects.
    This class provides methods to retrieve information about schemas
    from a backend service. It uses a session object to handle authenticated
    requests and supports retry mechanisms for robust communication.
    """

    def __init__(self, session: Union[Session, AuthenticatedSession]):
        self._session = session
        logger.info("SchemaAPI initialized with session: %s", type(session).__name__)

    def get_schema(self, *, name: str) -> V1SchemasResponse:
        logger.info("Retrieving schema with name: %s", name)
        kwargs: Dict[str, Any] = MethodFactory().get_schema(name)
        logger.debug("Request parameters for get_schema: %s", kwargs)
        response = execute_with_retry(
            session=self._session,
            request_func=self._session.get_httpx_client().request,
            **kwargs,
        )
        logger.info("Received response for get_schema: %s", response.text)
        return build_response(
            response=response, response_cls=DataModelFactory.get_schema()
        )

    def get_schemas(self) -> V1ListSchemasResponse:
        logger.info("Retrieving all schemas")
        kwargs: Dict[str, Any] = MethodFactory().get_schemas()
        logger.debug("Request parameters for get_models: %s", kwargs)
        response = execute_with_retry(
            session=self._session,
            request_func=self._session.get_httpx_client().request,
            **kwargs,
        )
        logger.info("Received response for get_models: %s", response.text)
        return build_response(
            response=response, response_cls=DataModelFactory.get_schemas()
        )

    def create_schema(
        self,
        *,
        name: str,
        schema_type: str,
        schema: List[SchemaItem],
    ) -> V1CreateSchemaResponse:
        """
        Create a new schema
        schema_name (str): The name of the schema
        schema_type (str): The type of the schema
        schemaItem (list): The keys required to create the table in the database.
            Each field may include an optional ``nullable`` flag (defaults to
            ``True``). Set ``nullable`` to ``False`` to mark a field as
            required (``NOT NULL`` in the database, strict schema validation).

        """
        logger.info("Creating schema with name: %s", name)
        body = V1CreateSchemaRequest(name=name, type=schema_type, schema=schema)
        kwargs: Dict[str, Any] = MethodFactory().create_schema()
        kwargs["json"] = body.model_dump(by_alias=True)

        logger.debug("Request payload for create_schema: %s", kwargs)
        response = execute_with_retry(
            session=self._session,
            request_func=self._session.get_httpx_client().request,
            **kwargs,
        )
        raw = build_response(response=response, response_cls=_ServerStatusResponse)
        result = V1CreateSchemaResponse(
            status=response.status_code,
            message=raw.status if raw else "",
            success=True,
            error={},
        )
        logger.info("Schema created successfully: %s", name)
        return result

    def delete_schema(self, *, name: str) -> V1DeleteSchemaResponse:
        """
        Delete schema by name
            Args:
                schema_name (str): The name of the schema to be deleted
            Returns:
                Optional[Union[Any, Schema]]: The deleted schema or None if the request failed.
        """
        logger.info("Deleting schema with name: %s", name)
        kwargs: Dict[str, Any] = MethodFactory().delete_schema(name=name)

        logger.debug("Request payload for delete_schema: %s", kwargs)
        response = execute_with_retry(
            session=self._session,
            request_func=self._session.get_httpx_client().request,
            **kwargs,
        )
        raw = build_response(response=response, response_cls=_ServerStatusResponse)
        result = V1DeleteSchemaResponse(
            status=response.status_code,
            message=raw.status if raw else "",
            success=True,
            error={},
        )
        logger.info("Deleted schema successfully: %s", name)
        return result
