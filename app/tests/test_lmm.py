# hämta responseParser och LLMOutput
from fastapi.testclient import TestClient
from app.llm.models import PipelineInput, PromptPayload
from app.llm.llm import PromptBuilder
from app.llm.llm import RawLLMOutput, ResponseParser, LLMRunner, PromptBuilder
from app.main import app

client = TestClient(app)


# Testar städning av kod
def test_response_parser_cleans_and_adds_signature(monkeypatch):
    # 1. Tvinga Python att tro att SmolLM körs för just för detta testet!
    # Detta ignorerar vad som faktiskt står i din .env-fil
    monkeypatch.setenv("MODEL_NAME", "smollm")

    # ARRANGE:
    # fake private eftersom vi bara behöver den i detta testet
    _o_q = "Vilken låt har högst tempo?"
    parser = ResponseParser()

    # här behöver vi skapa en fejk indata

    fake_input = RawLLMOutput(
        original_question=_o_q,
        raw_text="<|im_start|>assistant\nDet högsta tempot är 202.019.<|im_end|>",
    )
    # ACT:
    # nu kör vi fake_input genom ResponseParsen
    result = parser.invoke(fake_input)
    _r_q = result.question
    _r_a = result.answer
    # ASSERT:
    # verifiera att parsen har utfört sin städning av kod
    # 1. kolla så orginal frågan har kommit med
    assert _r_q == _o_q

    # 2. kolla så att städprocessen har gjorts
    assert "<|im_end|>" not in _r_a
    assert "<|im_start|>assistant" not in _r_a
    # Kolla att viktig data är kvar
    assert "Det högsta tempot är 202.019." in _r_a

    # kolla så att signaturen som ska adderas kommer med
    assert "krama varandra i trafiken!" in _r_a
    assert result.model == "smollm"


def test_prompt_builder_creates_correct_prompt():
    # ARRANGE
    builder = PromptBuilder()
    fake_input = PipelineInput(
        question="Vem är kungen av pop?",
        stats_text="Ingen statistik behövs",
        context="Du är en musikexpert.",
    )

    # ACT
    result = builder.invoke(fake_input)

    # ASSERT
    # Verifiera att resultatet är av rätt Pydantic-typ
    assert isinstance(result, PromptPayload)
    # Verifiera att prompten faktiskt bakade in vår data
    assert "Vem är kungen av pop?" in result.full_prompt
    assert "Ingen statistik behövs" in result.full_prompt
    assert "Du är en musikexpert." in result.full_prompt


# Testa att skicka tillbaka mockat svar
def test_llm_runner_with_mock(monkeypatch):
    def mock_invoke(self, data):
        return RawLLMOutput(original_question=data.question, raw_text="fejkat svar")

    monkeypatch.setattr(LLMRunner, "invoke", mock_invoke)
    runner = LLMRunner()

    class FakeInput:
        question = "Test"
        stats_text = "{}"
        provider = "huggingface"

    result = runner.invoke(FakeInput())
    assert "fejkat svar" in result.raw_text
