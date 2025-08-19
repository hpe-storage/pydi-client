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
- Managing schemas and embedding models

---

## 2. Non-Admin Operations: Setting Up DIClient

For non-admin tasks (querying collections, retrieving pipelines, similarity search), use `DIClient`. Note that `DIAdminClient` extends `DIClient`, but for read-only/search operations, use `DIClient`.

```python
from pydi_client.di_client import DIClient

# Initialize DIClient with the DI platform URI
client = DIClient(uri="https://your-di-instance.com:<port>")
```

**Use DIClient for:**
- Querying collections and pipelines
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

**Note: Currently creating new schemas is not supported. Require to use existing schemas available by default**


---

## 4. Getting List of Existing Embedding Models (Admin, RAG Workflow)

If you are setting up a RAG (Retrieval-Augmented Generation) pipeline, you need to select an embedding model supported by DI.

```python
# Get all embedding models available in the DI platform
models_response = admin_client.get_all_embedding_models()
print(models_response)
# Output: V1ListModelsResponse(
#     models=[ModelRecordSummary(name="example_model", ...), ...]
# )
```

Review the available models and select the one that fits your use case.

**Note: Currently creating new embedding models is not supported. Require to use existing models available by default**

---


## 5. Creating a Pipeline (Admin)

A pipeline defines how data is processed and ingested. Use `create_pipeline` in `DIAdminClient` to set up a pipeline.

```python
# Create a RAG pipeline
pipeline_response = admin_client.create_pipeline(
    name="example_rag_pipeline",
    pipeline_type="rag",  # or "metadata"
    model="example_model",  # Optional: specify embedding model
    custom_func="custom_processing_function",  # Optional
    event_filter_object_suffix=["*.txt", "*.pdf"],  # File types to ingest
    event_filter_max_object_size=10485760,  # Max file size in bytes
    schema="example_schema"  # Optional: specify schema
)

print(pipeline_response)
# Output: V1CreatePipelineResponse(
#     success=True,
#     message="Pipeline 'example_rag_pipeline' created successfully."
# )
```
**NOTE:**  
- For pipeline_type = "rag" (RAG workflows), `model` & `event_filter_max_object_size` are required. `schema` is optional and `custom_fuc` is not supported.
- For metadata pipelines, `custom_func` is required. `schema` & `event_filter_max_object_size` are optional and `model` is not supported.
---

## 6. Creating a Collection (Admin)

Collections are logical groupings of data that use a pipeline for ingestion and processing.

```python
# Create a collection using the pipeline created above
collection_response = admin_client.create_collection(
    name="example_collection",
    pipeline="example_rag_pipeline",
    buckets=[]  # You can assign buckets now or later
)

print(collection_response)
# Output: V1CollectionResponse(
#     name="example_collection",
#     pipeline="example_rag_pipeline",
#     buckets=[]
# )
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

---

## Summary

- Use `DIAdminClient` for all admin operations (CRUD on pipelines, collections, schemas, models).
- Use `DIClient` for non-admin operations (search, read-only queries).
- The typical workflow is: **Create Pipeline → Create Collection → Assign Buckets → Ingest Data → Search Data**.
- Refer to the API reference for more advanced features and error handling.

---