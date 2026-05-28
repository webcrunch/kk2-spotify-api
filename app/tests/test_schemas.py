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


def test_pipeline_input_rejects_wrong_type():
    with pytest.raises(ValidationError):
        PipelineInput(
            question=["En lista istället för en sträng;( "],
            stats_text="Den stora promptens äventyr",
        )


# _________ PROMPT PAYLOAD TESTER______________#


def test_prompt_payload_accepts_valid_data():
    data = PromptPayload(
        original_question="Fråga", full_prompt="Den stora promptens äventyr"
    )
    assert data.original_question == "Fråga"
    assert data.full_prompt == "Den stora promptens äventyr"


def test_prompt_payload_rejects_missing_field():
    with pytest.raises(ValidationError):
        PromptPayload(original_question="En lista istället för en sträng")


def test_prompt_payload_rejects_wrong_type():
    with pytest.raises(ValidationError):
        PromptPayload(
            original_question=["En lista istället för en sträng;( "],
            full_prompt="Den stora promptens äventyr",
        )


# _______ RAWLLMOUTPUT TEESTER _____#


def test_raw_llm_output_accepts_valid_data():
    data = RawLLMOutput(
        original_question="Super question", raw_text="Super duper raw text"
    )
    assert data.original_question == "Super question"
    assert data.raw_text == "Super duper raw text"


def test_raw_llm_output_rejects_missing_field():
    with pytest.raises(ValidationError):
        RawLLMOutput(original_question="Super question")


def test_raw_llm_output_rejects_wrong_type():
    with pytest.raises(ValidationError):
        RawLLMOutput(
            original_question=["Super question istället för en sträng;( "],
            full_prompt="Den stora promptens äventyr",
        )


# ____________  STRUCTURED RESPONSE TESTER INC .env fallback _______#


def test_structured_response_uses_default_model(monkeypatch):
    # Vi måste fajka att vi har satt en miljövariabel
    monkeypatch.delenv("MODEL_NAME", raising=False)

    # Här skapar vi modellen
    response = StructuredResponse(
        question="Den stora frågans äventyr", answer="Det stora svarets äventyr"
    )

    # verifjera så att fallbacken av modell kickar in
    assert response.model == "HuggingFaceTB/SmolLM2-135M-Instruct"


def test_structured_response_uses_env_variable(monkeypatch):
    # addera en fejkad miljövariabel
    monkeypatch.setenv("MODEL_NAME", "huggingintheface/astronomicalfa")

    # skapa modellen
    response = StructuredResponse(
        question="Den stora frågans äventyr", answer="Det stora svarets äventyr"
    )

    # verfiera så att den läser in fejkade variablen
    assert response.model == "huggingintheface/astronomicalfa"
