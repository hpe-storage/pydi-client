# Data Intelligence Concepts

## Collections
Logical domain for identifying a set of object metadata that is extracted and queried. Each Collection consists of the following:

- One or more Buckets associated with the Collection
- One Pipeline

A Collection may also define an output store, which is the destination bucket for transcription output, and an indexing mode for RAG collections (`HNSW` or `GPU_CAGRA`). When the indexing mode is not specified, it is auto-detected.

A Search query is executed against a Collection. The result from the Query will be based on search performed over all object metadata present within that Collection.

## Pipelines
Representation of the processing required to extract metadata for Data Intelligence. Each Pipeline consists of the following:

- One or more Event Filters that trigger the pipeline. A common use case for an event filter is to indicate the suffix for triggering extraction (e.g. "*.pdf" filter to trigger extraction from PDF files)

- One of either:
    - Model that identifies the model to use for the Pipeline, or,
    - Custom Function that identifies an external function used to extract metadata for the Pipeline

- One Schema describing the logical structure of the metadata to be extracted.

Pipelines are created with a `pipeline_type`, which determines the processing performed:

- `rag` - generates embeddings for semantic search, optionally chunked using `chunk_size` and `chunk_overlap`
- `transcribe-metadata` - transcribes image, audio or video content into text using a `prompt`
- `custom-function` - processes objects using a custom-function model and writes the result into the fields defined by the schema
- `metadata` - extracts metadata using a custom function

## Models
ML model used to process the object data, for example to extract embeddings or to transcribe media into text. A Model may be associated with a Pipeline Instance. This association is created when the Pipeline is instantiated, and cannot be modified for the lifetime of the Pipeline. The output generated from a Model is persisted within the Collection corresponding to the Pipeline.

Each Model advertises one or more capabilities (`Sentence-Similarity`, `Question-Answering`, `Image-Text-To-Text`, `Automatic-Speech-Recognition`, `Video-To-Text`, `Custom-Function`), which identify the pipeline types it can be used with.

## Schemas
Defines the structure of metadata to be extracted or queried. This is equivalent to the schema that identifies the columns/fields within a database table. Internally, the Collection organizes the metadata as defined by the schema for optimized RAG or Structured Query.

Each field in a Schema has a name, a type, and an optional `nullable` flag. A field with `nullable` set to `false` is required: the corresponding database column is created as `NOT NULL` and the field is validated strictly. Fields default to `nullable` true.


## Query
A query that provides an input in the form of natural language text, and expects a response in the form of a list of "result objects". A Query can be of either one of two types:

- RAG Query that returns the top search results which are semantically most similar to the input text. For example, a query for text-based RAG will generate text results. A RAG Query must be associated with a Model in order to perform similarity search on embeddings

- Structured Query that returns the search results from an exact match query on a structured table. The data type for a "result object" will be a record containing one or more fields derived from the table schema. (Note: Currently limit support is available for Structure Query)

A Query must be associated with a Collection, and executed in the context of a User (e.g. by providing S3 access key + secret key pair). The credentials provided in the context will be used to authenticate the User and authorize the results from the Query.