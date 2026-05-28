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


# _________ PROMPT PAYLOAD TESTER______________#


def test_prompt_payload_accepts_valid_data():
    data = PromptPayload(
        original_question="Fråga", full_prompt="Den stora promptens äventyr"
    )
    assert data.original_question == "Fråga"
    assert data.full_prompt == "Den stora promptens äventyr"


def test_prompt_payload_accepts_missing_field():
    with pytest.raises(ValidationError):
        PromptPayload(original_question="En lista istället för en sträng")


def test_prompt_payload_rejects_wrong_type():
    with pytest.raises(ValidationError):
        PromptPayload(
            original_question=["En lista istället för en sträng;( "],
            full_prompt="Den stora promptens äventyr",
        )
