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


def test_pipeline_input_accepts_valid_data():
    data = PipelineInput(question="Din stora hamster", stats_text="Data")
    assert data.question == "Din stora hamster"
    assert data.stats_text == "Data"


def test_pipeline_input_reject_missing_field():
    with pytest.raises(ValidationError):
        PipelineInput(question="Din stora hamster")
    # Denna ska smälla för vi har ingen stats_text
