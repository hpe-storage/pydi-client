# Copyright Hewlett Packard Enterprise Development LP

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class SchemaListItem(BaseModel):
    """
    Represents a single schema item in the list schemas response.

    Attributes:
        id (Optional[str]): Unique identifier of the schema.
        name (str): Name of the schema.
    """

    id: Optional[str] = Field(default=None, description="schema id")
    name: str = Field(..., description="schema name")


class V1ListSchemasResponse(BaseModel):
    """
    Represents a response containing a list of schema records.

    Attributes:
        schemas (List[SchemaListItem]): List of available schemas with id and name.
    """

    schemas: List[SchemaListItem]


class SchemaItem(BaseModel):
    """
    Represents a single field definition inside a schema.

    Attributes:
        name (str): Field name in the schema definition.
        type (str): Field type in the schema definition.
    """

    name: str = Field(..., description="field name")
    type: str = Field(..., description="field type")


class V1SchemasResponse(BaseModel):
    """
    Represents a detailed schema response.

    This model contains the schema name, schema type, and the list of
    schema fields returned by the API.

    Attributes:
        name (str): Name of the schema.
        type (Optional[str]): Schema type (for example, `rag` or `transcribe-metadata`).
        schema_fields (List[SchemaItem]): List of schema fields (serialized as `schema`).
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="schema name")
    type: Optional[str] = Field(
        default=None,
        description="Schema type (e.g., 'rag', 'transcribe-metadata')",
    )
    schema_fields: List[SchemaItem] = Field(
        ..., alias="schema", description="list of schema fields"
    )


class V1CreateSchemaRequest(BaseModel):
    """
    Request body for creating a new schema.

    Attributes:
        name (str): Name of the schema to create.
        type (str): Schema type (for example, `rag` or `transcribe-metadata`).
        schema_fields (List[SchemaItem]): List of schema fields (serialized as `schema`).
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="schema name")
    type: str = Field(..., description="schema type (e.g., 'rag', 'transcribe-metadata')")
    schema_fields: List[SchemaItem] = Field(..., alias="schema", description="list of schema fields")


class V1CreateSchemaResponse(BaseModel):
    """
    Response returned after attempting to create a schema.

    Attributes:
        success (Optional[bool]): Indicates whether schema creation succeeded.
        message (Optional[str]): Additional information about the operation.
    """

    success: Optional[bool] = None
    message: Optional[str] = None

