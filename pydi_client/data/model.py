# Copyright Hewlett Packard Enterprise Development LP

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class ModelTags(Enum):
    SENTENCE_SIMILARITY = "Sentence-Similarity"
    QUESTION_ANSWERING = "Question-Answering"
    IMAGE_TEXT_TO_TEXT = "Image-Text-To-Text"
    AUTOMATIC_SPEECH_RECOGNITION = "Automatic-Speech-Recognition"

class V1ModelsResponse(BaseModel):
    """
    Response model for listing available models.
    This model contains fields to represent the system model name, model name,
    capabilities, dimensionality, maximum tokens supported by the model, and the version of the model.
    Attributes:
        name (str): System model name.
        modelName (str): Model name.
        capabilities (List[str]): List of capabilities such as embedding, large language model, etc.
        version (str): Model version.
        communicationType (str): API communication type identifier for the model.
        dimension (int): Model dimensionality.
        contextLength (int): Context length for the model.
        temperature (float): Temperature setting for the model.
        topK (int): Top-k setting for the model.
        topP (float): Top-p setting for the model.
        maximumTokens (int): Maximum token size supported by the model.
        timeout (int): API request timeout for the model.
        language (str): Language supported by the model.
        sampleRate (int): Sampling rate for the ASR model.
        automaticPunctuation (bool): Enable automatic punctuation in the ASR model.
    """

    name: str = Field(..., description="system model name")
    modelName: str = Field(..., description="model name")
    capabilities: List[str] = Field(...,
                                    description="Sentence-Similarity, Question-Answering, Image-Text-To-Text etc")
    version: str = Field(..., description="model version")
    communicationType: str = Field(..., description="API communication type identifier for the model.")
    dimension: Optional[int] = Field(..., description="model dimensionality")
    contextLength: Optional[int] = Field(..., description="context length for the model")
    temperature: Optional[float] = Field(..., description="temperature setting for the model")
    topK: Optional[int] = Field(..., description="top-k setting for the model")
    topP: Optional[float] = Field(..., description="top-p setting for the model")
    maximumTokens: Optional[int] = Field(...,
                               description="max token size supported by the model")
    timeout: Optional[int] = Field(..., description="API request timeout for the model.")
    language: Optional[str] = Field(..., description="Language supported by the model.")
    sampleRate: Optional[int] = Field(..., description="Sampling rate for the ASR model.")
    automaticPunctuation: Optional[bool] = Field(..., description="Enable automatic punctuation in the ASR model.")



class ModelRecordSummary(BaseModel):
    """
    Represents a summary of a model record.
    Attributes:
        id (str): Unique identifier for the model record.
        name (str): Name of the model record.
    """
    id: str
    name: str


class V1ListModelsResponse(BaseModel):
    """
    Response model for listing available models.
    This model contains a list of model records.
    Attributes:
        models (List[ModelRecordSummary]): List of model records.
    """
    models: List[ModelRecordSummary]
