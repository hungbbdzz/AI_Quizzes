import os
import uuid

import pytest


os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeStorageBucket:
    def __init__(self, store):
        self._store = store

    def upload(self, path, data, opts):
        self._store[path] = {"data": data, "opts": opts}

    def get_public_url(self, path):
        return f"https://fake.storage/{path}"


class FakeStorage:
    def __init__(self):
        self._buckets = {}

    def from_(self, bucket):
        if bucket not in self._buckets:
            self._buckets[bucket] = FakeStorageBucket({})
        return self._buckets[bucket]


class FakeTable:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self._filters = []
        self._single = False
        self._update = None
        self._delete = False
        self._last = None

    def select(self, *args, **kwargs):
        return self

    def insert(self, records):
        if isinstance(records, dict):
            records = [records]
        table = self.db.setdefault(self.table_name, [])
        out = []
        for record in records:
            row = dict(record)
            if "id" not in row:
                row["id"] = str(uuid.uuid4())
            if "created_at" not in row:
                row["created_at"] = "2026-05-06T00:00:00Z"
            table.append(row)
            out.append(row)
        self._last = out
        return self

    def update(self, values):
        self._update = values
        return self

    def delete(self):
        self._delete = True
        return self

    def eq(self, field, value):
        self._filters.append((field, value))
        return self

    def order(self, *args, **kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        table = self.db.get(self.table_name, [])

        def match(row):
            for field, value in self._filters:
                if "." in field:
                    key = field.split(".", 1)[-1]
                else:
                    key = field
                if row.get(key) != value:
                    return False
            return True

        filtered = [row for row in table if match(row)]

        if self._update is not None:
            updated = []
            for row in filtered:
                row.update(self._update)
                updated.append(row)
            data = updated
        elif self._delete:
            remaining = [row for row in table if not match(row)]
            self.db[self.table_name] = remaining
            data = filtered
        elif self._last is not None:
            data = self._last
        else:
            data = filtered

        if self._single:
            data = data[0] if data else None

        return FakeResponse(data=data)


class FakeSupabase:
    def __init__(self):
        self.db = {}
        self.storage = FakeStorage()

    def table(self, name):
        return FakeTable(self.db, name)

    def rpc(self, name, params):
        return FakeResponse(data=[])


@pytest.fixture
def fake_supabase():
    return FakeSupabase()


@pytest.fixture
def patch_supabase_admin(monkeypatch, fake_supabase):
    import app.services.document_service as document_service

    monkeypatch.setattr(document_service, "get_supabase_admin_client", lambda: fake_supabase)
    return fake_supabase


@pytest.fixture
def mock_embeddings(monkeypatch):
    import app.services.ai_service as ai_service

    class FakeEmbeddings:
        def embed_documents(self, texts):
            return [[float(i)] * 3 for i, _ in enumerate(texts)]

        def embed_query(self, text):
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr(ai_service, "_get_embeddings", lambda: FakeEmbeddings())
    return FakeEmbeddings()
