import json

import pytest
from langchain_core.runnables import RunnableLambda

import app.services.ai_service as ai_service


def make_llm_with_outputs(outputs):
    iterator = iter(outputs)

    def _respond(_):
        try:
            content = next(iterator)
        except StopIteration:
            content = outputs[-1]
        return type("Resp", (), {"content": content})()

    return RunnableLambda(_respond)


def test_parse_json_response_strips_fences():
    raw = "```json\n[{\"front\":\"A\",\"back\":\"B\"}]\n```"
    parsed = ai_service._parse_json_response(raw)
    assert parsed == [{"front": "A", "back": "B"}]


@pytest.mark.asyncio
async def test_generate_quiz_retries_invalid_json(monkeypatch):
    outputs = [
        "not json",
        json.dumps(
            [
                {
                    "question": "Q1",
                    "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                    "correct_answer": "A",
                }
            ]
        ),
    ]

    monkeypatch.setattr(ai_service, "_get_llm", lambda temperature=0.5: make_llm_with_outputs(outputs))

    result = await ai_service.generate_quiz(
        raw_text="Noi dung test",
        num_questions=1,
        difficulty="easy",
    )

    assert len(result) == 1
    assert result[0]["correct_answer"] == "A"


@pytest.mark.asyncio
async def test_generate_flashcards_parses_json(monkeypatch):
    outputs = [
        json.dumps(
            [
                {"front": "Tu khoa", "back": "Dinh nghia"},
                {"front": "Khai niem", "back": "Giai thich"},
            ]
        )
    ]

    monkeypatch.setattr(ai_service, "_get_llm", lambda temperature=0.6: make_llm_with_outputs(outputs))

    result = await ai_service.generate_flashcards(raw_text="Noi dung", num_flashcards=2)
    assert len(result) == 2
    assert result[0]["front"] == "Tu khoa"
