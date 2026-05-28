# hämta responseParser och LLMOutput
from fastapi.testclient import TestClient

from app.llm.llm import RawLLMOutput, ResponseParser, LLMRunner
from app.main import app

client = TestClient(app)


# Test 1 : testar städning av kod
def test_response_parser_cleans_and_adds_signature():
    # ARRANGE:
    # fake private eftersom vi bara behöver den i detta testet
    _o_q = "Vilken låt har högst tempo?"
    parser = ResponseParser()

    # här behöver vi skapa en fejk indata

    fake_input = RawLLMOutput(
        original_question=_o_q,
        raw_text="<|im_start|> assistant\n Det högsta tempot är 202.019. <|im_end|>",
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
    assert "<|im_start|assistant>" not in _r_a
    # Kolla att viktig data är kvar
    assert "Det högsta tempot är 202.019." in _r_a

    # kolla så att signaturen som ska adderas kommer med
    assert "krama varnadra i trafiken" in _r_a


# Test 2 : Testar mina endpoints
def test_ask_ai_without_data_return_400():
    response = client.post("/ai/ask", json={"question": "Test?"})
    assert response.status_code == 400
