# Copyright Hewlett Packard Enterprise Development LP

from pydi_client.data.collection_manager import V1PipelineResponse
from pydi_client.data.pipeline import V1CreatePipeline
from pydi_client.data.schema import V1SchemasResponse


def test_schema_wire_key_uses_non_conflicting_model_attributes():
    models_and_fields = (
        (V1PipelineResponse, "schema_name"),
        (V1CreatePipeline, "schema_name"),
        (V1SchemasResponse, "schema_fields"),
    )

    for model, field_name in models_and_fields:
        assert "schema" not in model.model_fields
        field = model.model_fields[field_name]
        assert field.validation_alias == "schema"
        assert field.serialization_alias == "schema"
