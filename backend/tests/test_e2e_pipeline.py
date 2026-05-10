from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

import app.services.document_service as document_service


@pytest.mark.asyncio
async def test_process_upload_happy_path(patch_supabase_admin, mock_embeddings):
    content = b"Hoc sinh can on tap bai hom nay. Day la van ban mau."
    upload = UploadFile(
        filename="sample.txt",
        file=BytesIO(content),
        headers=Headers({"content-type": "text/plain"}),
    )

    doc = await document_service.process_upload(upload, user_id="user-1")

    assert doc["status"] == "ready"
    assert doc["file_type"] == "txt"
    assert doc["file_url"].startswith("https://fake.storage/")

    db = patch_supabase_admin.db
    assert len(db.get("documents", [])) == 1
    assert len(db.get("document_chunks", [])) >= 1
