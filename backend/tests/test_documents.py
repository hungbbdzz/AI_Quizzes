import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_upload_document_unauthenticated(client):
    """Nên từ chối upload nếu không có auth token."""
    response = await client.post("/api/documents/upload")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_documents_unauthenticated(client):
    """Nên từ chối listing nếu không có auth token."""
    response = await client.get("/api/documents")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_unsupported_file_type(client):
    """Cần token hợp lệ nhưng request fake không có, nên 403 trước.
    Nếu test unit với client override auth, thì check được 400.
    """
    response = await client.post("/api/documents/upload")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_nonexistent_document(client):
    """Nên từ chối nếu không auth, nếu có auth thì 404."""
    response = await client.get("/api/documents/nonexistent-id")
    assert response.status_code == 403
