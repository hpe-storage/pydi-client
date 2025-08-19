# Data Intelligence Concepts

## Collections
Logical domain for identifying a set of object metadata that is extracted and queried. Each Collection consists of the following:

- One or more Buckets associated with the Collection
- One Pipeline

A Search query is executed against a Collection. The result from the Query will be based on search performed over all object metadata present within that Collection.

## Pipelines
Representation of the processing required to extract metadata for Data Intelligence. Each Pipeline consists of the following:

- One or more Event Filters that trigger the pipeline. A common use case for an event filter is to indicate the suffix for triggering extraction (e.g. "*.pdf" filter to trigger extraction from PDF files)

- One of either:
    - Model that identifies the embedding model to use for the Pipeline, or,
    - Custom Function (custom function is not supported currently. However the API requires a dummy custom function string as input. Ex - "custom_processing_function")


- One Schema describing the logical structure of the metadata to be extracted.

## Embedding Models
ML model used to extract embeddings from the object data. A Model may be associated with a Pipeline Instance. This association is created when the Pipeline is instantiated, and cannot be modified for the lifetime of the Pipeline. The embeddings generated from a Model are persisted within the Collection corresponding to the Pipeline.

## Schemas
Defines the structure of metadata to be extracted or queried. This is equivalent to the schema that identifies the columns/fields within a database table. Internally, the Collection organizes the metadata as defined by the schema for optimized RAG or Structured Query.


## Query
A query that provides an input in the form of natural language text, and expects a response in the form of a list of "result objects". A Query can be of either one of two types:

- RAG Query that returns the top search results which are semantically most similar to the input text. For example, a query for text-based RAG will generate text results. A RAG Query must be associated with a Model in order to perform similarity search on embeddings

- Structured Query that returns the search results from an exact match query on a structured table. The data type for a "result object" will be a record containing one or more fields derived from the table schema. (Note: Currently limit support is available for Structure Query)

A Query must be associated with a Collection, and executed in the context of a User (e.g. by providing S3 access key + secret key pair). The credentials provided in the context will be used to authenticate the User and authorize the results from the Query.