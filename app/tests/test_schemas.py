import pytest
import os
from pydantic import ValidationError

# from app.llm.llm import RawLLMOutput
from app.llm.models import (
    PipelineInput,
    PromptPayload,
    RawLLMOutput,
    StructuredResponse,
)

# _____ PIPELINE TESTER ______#


def pipeline_input_accepts_valid_data():
    data = PipelineInput(question="Din stora hamster", stats_text="Data")
    assert data.question == "Din stora hamster"
    assert data.stats_text == "Data"
