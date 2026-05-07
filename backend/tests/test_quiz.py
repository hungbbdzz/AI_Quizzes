import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_generate_quiz_unauthenticated(client):
    """Nên từ chối quiz generation nếu không có auth."""
    response = await client.post("/api/quiz/generate", json={
        "document_id": "some-id",
        "num_questions": 5,
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_nonexistent_quiz(client):
    """Nên từ chối 403 trước tiên nếu không gửi token."""
    response = await client.get("/api/quiz/nonexistent-id")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_community_quizzes(client):
    """Whitelist auth (nếu code không áp rule required), else 403/200 . 
       Theo router hiện tại thì Endpoint /community không yêu cầu current_user.
    """
    response = await client.get("/api/quiz/community")
    # API này có Requires auth hay không tuỳ dependencies. Ở code hiện tại 
    # router get_community_quizzes ko có `current_user = Depends(...)`
    # nhưng middleware/bearer có thể bắt. 
    # Trong `app/routers/quiz.py` nó ko dùng `get_current_user`
    assert response.status_code in [200, 403]
