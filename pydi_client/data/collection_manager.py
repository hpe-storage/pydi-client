# Copyright Hewlett Packard Enterprise Development LP

from pydantic import BaseModel, ConfigDict, Field, RootModel
from typing import List, Dict, Optional, Any


class V1DeleteCollectionResponse(BaseModel):
    """
    Response model for deleting a collection.
    This model contains fields to indicate the status of the delete operation,
    any errors that occurred, and a message providing additional information.
    Attributes:
        status (Optional[str]): Status of the delete operation.
        Status (Optional[str]): Alternative case for status of the delete operation.
        Error (Optional[Dict[Any, Any]]): Error message if the delete operation fails.
        success (Optional[bool]): Indicates if the delete operation was successful.
        message (Optional[str]): Message providing additional information about the operation.
    """
    status: Optional[str] = Field(
        default_factory=str, description="Status of the delete operation"
    )
    Status: Optional[str] = Field(
        default_factory=str,
        description="Status of the delete operation (alternative case)",
    )
    Error: Optional[Dict[Any, Any]] = Field(
        default_factory=dict, description="Error message if the delete operation fails"
    )
    success: Optional[bool] = Field(
        default=None, description="Indicates if the delete operation was successful"
    )
    message: Optional[str] = Field(
        default=None, description="Message providing additional information about the operation"
    )


class V1CreateCollection(BaseModel):
    """
    Represents a request to create a collection.
    Attributes:
        name (str): Name of the collection.
        pipeline (str): Pipeline associated with the collection.
        buckets (Optional[List[str]]): Optional list of buckets associated with the collection.
        outputStore (Optional[str]): Output bucket for transcription results (transcribe usecase).
        indexingMode (Optional[str]): Indexing mode for RAG collections (e.g., HNSW, GPU_CAGRA). Auto-detected if omitted.
    """
    name: str
    pipeline: str
    buckets: Optional[List[str]]
    outputStore: Optional[str] = Field(
        default=None,
        description="Output bucket for transcription results",
    )
    indexingMode: Optional[str] = Field(
        default=None,
        description="Indexing mode for RAG collections (e.g., HNSW, GPU_CAGRA). Auto-detected if omitted.",
    )


class V1CollectionResponse(BaseModel):
    """
    Represents a response containing collection information.
    This model contains fields to represent the collection name, pipeline, and an optional list of buckets
    associated with the collection.
    Attributes:
        name (str): Name of the collection.
        pipeline (str): Pipeline associated with the collection.
        buckets (Optional[List[str]]): Optional list of buckets associated with the collection.
        outputStore (Optional[str]): Output bucket for transcription results (transcribe usecase).
        indexingMode (Optional[str]): Indexing mode for RAG collections (e.g., HNSW, GPU_CAGRA).
    """
    name: str
    pipeline: str
    buckets: Optional[List[str]] = Field(
        default_factory=list,
        description="List of buckets associated with the collection",
    )
    outputStore: Optional[str] = Field(
        default=None,
        description="Output bucket for transcription results",
    )
    indexingMode: Optional[str] = Field(
        default=None,
        description="Indexing mode for RAG collections (e.g., HNSW, GPU_CAGRA)",
    )


class BucketUpdateRequest(BaseModel):
    """
    Represents a request to update the buckets of a collection.
    Attributes:
        name (str): Name of the collection.
        buckets (List[str]): List of buckets to be associated with the collection.
    """
    name: str
    buckets: List[str]


class V1PipelineResponse(BaseModel):
    """
    Represents a response containing pipeline information.
    This model contains fields to represent the pipeline name, type, model, custom function,
    event filter criteria, and schema associated with the pipeline.
    Attributes:
        name (str): Name of the pipeline.
        type (str): Type of the pipeline.
        model (Optional[str]): Optional model associated with the pipeline.
        customFunction (Optional[str]): Optional custom function for the pipeline.
        eventFilter (Dict[str, Any]): Event filter criteria for the pipeline.
        schema_name (str): Schema associated with the pipeline (serialized as 'schema').
        prompt (Optional[str]): Prompt for transcribe pipelines.
        chunkSize (Optional[int]): Chunk size for RAG pipelines.
        chunkOverlap (Optional[int]): Chunk overlap for RAG pipelines.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str
    type: str
    model: Optional[str] = Field(default=None)
    customFunction: Optional[str] = Field(default=None)
    eventFilter: Dict[str, Any]
    schema_name: str = Field(alias="schema")
    prompt: Optional[str] = Field(default=None, description="Prompt for transcribe pipelines")
    chunkSize: Optional[int] = Field(default=None, description="Chunk size for RAG pipelines")
    chunkOverlap: Optional[int] = Field(default=None, description="Chunk overlap for RAG pipelines")


class ListCollectionItem(BaseModel):
    """
    Represents a summary of a collection item.
    Attributes:
        id (Optional[str]): Unique identifier for the collection item.
        name (Optional[str]): Name of the collection item.
    """
    id: Optional[str] = Field(None, description="collection id")
    name: Optional[str] = Field(None, description="collection name")


class ListCollection(RootModel[List[ListCollectionItem]]):
    """
    Response model for listing available collections.
    This model contains a list of collection items.
    Attributes:
        root (List[ListCollectionItem]): List of collection items.
    """
    root: List[ListCollectionItem] = Field(
        ...,
        examples=[
            [{"id": "1", "name": "collection1"}, {"id": "2", "name": "collection2"}]
        ],
    )


class ListPipeline(BaseModel):
    """
    Represents a summary of a pipeline.
    Attributes:
        id (Optional[str]): Unique identifier for the pipeline.
        name (Optional[str]): Name of the pipeline.
    """
    id: Optional[str] = Field(None, description="pipeline id")
    name: Optional[str] = Field(None, description="pipeline name")


class ListPipelines(RootModel[List[ListPipeline]]):
    """
    Response model for listing available pipelines.
    This model contains a list of pipelines.
    Attributes:
        root (List[ListPipeline]): List of pipelines.
    """
    root: List[ListPipeline] = Field(
        ...,
        examples=[[{"id": "1", "name": "pipeline1"}, {"id": "2", "name": "pipeline2"}]],
    )
