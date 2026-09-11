# Data Intelligence SDK Tutorial

This tutorial provides a step-by-step guide for using the Data Intelligence (DI) SDK, focusing on both administrative and non-administrative workflows. It covers client setup, pipeline and collection creation, bucket assignment, and similarity search.

## Logging
di_sdk.log will be created with detailed logs in CWD. Set env variable LOG_LEVEL to adjust the logging. (For ex: export LOG_LEVEL=DEBUG to enable debug logging for more detailed analysis)

## 1. Admin Operations: Setting Up DIAdminClient

Administrative operations (CRUD for pipelines, collections, schemas, models) require the `DIAdminClient`. This client needs authentication credentials.

```python
from pydi_client.di_client import DIAdminClient

# Initialize DIAdminClient with URI, username, and password
admin_client = DIAdminClient(
    uri="https://your-di-instance.com:<port>",
    username="admin_user",
    password="your_password"
)
```

**Use DIAdminClient for:**
- Creating/deleting pipelines and collections
- Assigning/unassigning buckets
- Creating, deleting, listing and getting schemas

---

## 2. Non-Admin Operations: Setting Up DIClient

For non-admin tasks (querying collections, retrieving pipelines, similarity search), use `DIClient`. Note that `DIAdminClient` extends `DIClient`, but for read-only/search operations, use `DIClient`.

```python
from pydi_client.di_client import DIClient

# Initialize DIClient with the DI platform URI
client = DIClient(uri="https://your-di-instance.com:<port>")
```

**Use DIClient for:**
- Querying collections, pipelines and models
- Performing similarity searches

---

## 3. Getting List of Existing Schemas (Admin)

Before creating a pipeline, you may want to see which schemas are available in your DI instance. This helps you select the correct schema for your workflow.

```python
# Get all schemas available in the DI platform
schemas_response = admin_client.get_all_schemas()
print(schemas_response)
# Output: V1ListSchemasResponse(
#     schemas=[SchemaRecordSummary(name="example_schema", ...), ...]
# )
```

You can inspect the schema names and details to choose the appropriate schema for your pipeline.

**Schema API support in SDK:**
- Supported: `get_all_schemas()`, `get_schema(name=...)`, `create_schema(...)`, `delete_schema(name=...)`


---

## 4. Getting List of Existing Models

Before creating a pipeline, select a model that matches your workflow. `get_all_models()` and `get_model()`
return both embedding models and LLMs, and do not require authentication, so they are available on `DIClient`
as well as `DIAdminClient`.

```python
from pydi_client.data.model import ModelTags

# Get all models available in the DI platform
models_response = client.get_all_models()
print(models_response)
# Output: V1ListModelsResponse(
#     models=[ModelRecordSummary(name="example_model", ...), ...]
# )

# Filter the embedding models based on their capabilities.
embedding_models = list(filter(lambda model: ModelTags.SENTENCE_SIMILARITY.value in client.get_model(name=model.name).capabilities, models_response.models))
# Output: 
# embedding_models = [
#   ModelRecordSummary(name="example_embedding_model", ...), 
# ...] 
```

Use `get_model()` to inspect a single model in detail:

```python
model = client.get_model(name="example_model")
print(model.capabilities, model.dimension, model.contextLength, model.endpoint)
```

Available capability tags (`pydi_client.data.model.ModelTags`):

| Tag | Value | Typical pipeline type |
|-----|-------|-----------------------|
| `SENTENCE_SIMILARITY` | `Sentence-Similarity` | `rag` |
| `QUESTION_ANSWERING` | `Question-Answering` | `rag` |
| `IMAGE_TEXT_TO_TEXT` | `Image-Text-To-Text` | `transcribe-metadata` |
| `AUTOMATIC_SPEECH_RECOGNITION` | `Automatic-Speech-Recognition` | `transcribe-metadata` |
| `VIDEO_TO_TEXT` | `Video-To-Text` | `transcribe-metadata` |
| `CUSTOM_FUNCTION` | `Custom-Function` | `custom-function` |

**Note**: `get_all_embedding_models()` and `get_embedding_model()` on `DIAdminClient` are deprecated and
will be removed in a future release. They emit a `DeprecationWarning`; use `get_all_models()` and
`get_model()` instead.

**Note: Currently creating new models is not supported. Require to use existing models available by default**

---


## 5. Creating a Pipeline (Admin)

A pipeline defines how data is processed and ingested. Use `create_pipeline` in `DIAdminClient` to set up a pipeline.

```python
# Create a RAG pipeline
pipeline_response = admin_client.create_pipeline(
    name="example_rag_pipeline",
    pipeline_type="rag",
    model="example_model",
    event_filter_object_suffix=["*.txt", "*.pdf"],  # File types to ingest
    event_filter_max_object_size=10485760,  # Max file size in bytes
    schema="example_schema"
)

print(pipeline_response)
# Output: V1CreatePipelineResponse(
#     success=True,
#     message="Pipeline 'example_rag_pipeline' created successfully."
# )
```

### Transcribe pipeline (images)

```python
pipeline_response = admin_client.create_pipeline(
    name="example_transcribe_pipeline",
    pipeline_type="transcribe-metadata",
    model="supported_transcribe_model",
    event_filter_object_suffix=["*.jpg", "*.png", "*.jpeg"],
    event_filter_max_object_size=10737418240,  # Optional: max file size in bytes
    schema="your_transcribe_schema",  # Use a transcribe-compatible schema
    prompt="Extract text from image files.",
)
```

### Transcribe pipeline (video)

```python
pipeline_response = admin_client.create_pipeline(
    name="example-transcribe-video-metadata",
    pipeline_type="transcribe-metadata",
    model="parakeet-1_1b-rnnt-multilingual-asr",
    event_filter_object_suffix=["*.mp4"],
    event_filter_max_object_size=524288000,
    schema="default-transcribe-metadata-schema",
    prompt="Transcribe the speech content into text."
)
```

### NIM RAG pipeline

```python
pipeline_response = admin_client.create_pipeline(
    name="example-nim-rag-pipeline",
    pipeline_type="rag",
    model="llama-nemotron-embed-1b-v2",
    event_filter_object_suffix=["*.pdf"],
    event_filter_max_object_size=1000000,
    schema="default-rag-schema",
    chunk_size=512,
    chunk_overlap=50
)
```

### Custom-function pipeline

```python
pipeline_response = admin_client.create_pipeline(
    name="example-custom-function-pipeline",
    pipeline_type="custom-function",
    model="di-custom-function-model",
    event_filter_object_suffix=["*.jpg"],
    schema="my-custom-function-schema"
)
```

**NOTE:**

- `name`, `pipeline_type`, `event_filter_object_suffix` and `schema` are required for every pipeline type.
- `event_filter_max_object_size` is optional.
- For `pipeline_type="rag"`, `model` is required and `custom_func` is not supported. Use `chunk_size` and
  `chunk_overlap` to control chunking behavior.
- For `pipeline_type="metadata"`, `custom_func` is required and `model` is not supported.
- For `pipeline_type="transcribe-metadata"`, provide a transcribe `prompt` and choose a model supported by
  your deployment (for example an `Image-Text-To-Text`, `Automatic-Speech-Recognition` or `Video-To-Text`
  model), together with a transcribe-compatible schema.
- For `pipeline_type="custom-function"`, both `model` and `schema` are mandatory.

### Handling validation errors

Invalid pipeline input raises `PipelineValidationError`, whether the problem is detected locally (missing or
unexpected arguments, wrong types) or reported by the server as HTTP 422. The exception collects every
problem into a single message.

```python
from pydi_client.errors import PipelineValidationError

try:
    admin_client.create_pipeline(
        name="example_rag_pipeline",
        pipeline_type="rag",
        event_filter_object_suffix=["*.pdf"],
    )
except PipelineValidationError as error:
    print(error)          # Pipeline validation failed (client): schema: Field required
    print(error.source)   # "client" or "server"
    print(error.errors)   # [{"type": "missing", "loc": ["schema"], "msg": "Field required"}]
    print(error.status_code)  # HTTP status code when source == "server"
```

---

## 6. Creating a Collection (Admin)

Collections are logical groupings of data that use a pipeline for ingestion and processing.

```python
# Create a collection using the pipeline created above
collection_response = admin_client.create_collection(
    name="example_collection",
    pipeline="example_rag_pipeline",
    buckets=[],  # You can assign buckets now or later
)

print(collection_response)
# Output: V1CollectionResponse(
#     name="example_collection",
#     pipeline="example_rag_pipeline",
#     buckets=[]
# )
```

For transcribe collections, set `output_store` to the destination bucket where transcription output is written:

```python
collection_response = admin_client.create_collection(
    name="example_transcribe_collection",
    pipeline="example_transcribe_pipeline",
    buckets=["example-input-bucket"],
    output_store="example-output-bucket",
)
```

For RAG collections you can pin the vector index type with `indexing_mode` (`"HNSW"` or `"GPU_CAGRA"`).
When omitted, the indexing mode is auto-detected from the deployment.

```python
collection_response = admin_client.create_collection(
    name="example_gpu_collection",
    pipeline="example_rag_pipeline",
    buckets=["example-input-bucket"],
    indexing_mode="GPU_CAGRA",
)
```

---

## 7. Assigning S3 Buckets to a Collection (Admin)

Assigning buckets triggers the pipeline and enables data ingestion. Buckets typically refer to S3 buckets from X10K.

```python
# Assign S3 buckets to the collection
bucket_update_response = admin_client.assign_buckets_to_collection(
    collection_name="example_collection",
    buckets=["homefleet-bucket1", "homefleet-bucket2"]
)

print(bucket_update_response)
# Output: BucketUpdateResponse(
#     success=True,
#     message="Buckets assigned successfully to collection 'example_collection'."
# )
```

**Note:** You can also unassign buckets using `unassign_buckets_from_collection`.

---

## 8. Performing Similarity Search (User)

Once data is ingested, users can perform similarity searches using the `DIClient`. This operation requires S3 access and S3 secret keys for authorization of data from X10K buckets. Only the authozided data can be retrieved using similarity search.

```python
# Perform a similarity search in a collection
results = client.similarity_search(
    query="machine learning",
    collection_name="example_collection",
    top_k=5,
    access_key="your_access_key",
    secret_key="your_secret_key",
)

print(results)
# Output: List of dictionaries with top-k similar results
# [
#     {
#         "dataChunk": "chunk1",
#         "score": 0.9,
#         "chunkMetadata": {
#             "objectKey": "value",
#             "startCharIndex": 1,
#             "endCharIndex": 2,
#             "bucketName": "string",
#             "pageLabel": "string",
#             "versionId": "string",
#         }
#     },
#     ...
# ]
```
## 9. Create schema (Admin)

```python
schema_response = admin_client.create_schema(
    name="yolo-detection-schema",
    schema_type="custom-function",
    schema=[
        {"name": "id", "type": "varchar"},
        {"name": "content", "type": "varchar"},
        {"name": "embedding", "type": "array(real)"},
    ]
)

print(schema_response)
# Output: V1CreateSchemaResponse(
#     status=200,
#     message="Schema created successfully",
#     success=True,
#     error={}
# )
```

You can optionally mark individual fields as required by setting `nullable: False`. Fields with `nullable: False` are created as `NOT NULL` in the database and validated strictly, while fields where `nullable` is omitted default to `True` (non-strict validation).

```python
schema_response = admin_client.create_schema(
    name="yolo-detection-schema",
    schema_type="custom-function",
    schema=[
        {"name": "id", "type": "varchar", "nullable": False},   # required
        {"name": "content", "type": "varchar"},                 # optional (nullable=True)
        {"name": "embedding", "type": "array(real)"},           # optional (nullable=True)
    ]
)
```

## 10. Delete schema (Admin)

```python
res = admin_client.delete_schema(name="yolo-detection-schema")
```

---

## Summary

- Use `DIAdminClient` for all admin operations (CRUD on pipelines, collections, schemas, models).
- Use `DIClient` for non-admin operations (search, read-only queries).
- The typical workflow is: **Create Pipeline → Create Collection → Assign Buckets → Ingest Data → Search Data**.
- Refer to the API reference for more advanced features and error handling.

---
