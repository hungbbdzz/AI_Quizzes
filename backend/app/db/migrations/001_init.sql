-- ============================================================
-- AI Quiz & Flashcard System: Initial Database Migration
-- ============================================================

-- Bật extension pgvector
create extension if not exists vector;

-- ============================================================
-- Users (quản lý bởi Supabase Auth, bảng này extend thêm)
-- ============================================================
create table if not exists users (
  id uuid references auth.users(id) on delete cascade primary key,
  full_name text,
  email text,
  created_at timestamptz default now()
);

-- ============================================================
-- Documents
-- ============================================================
create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  file_name text not null,
  file_url text,
  file_type text,  -- 'pdf' | 'docx' | 'txt'
  raw_text text,
  summary_text text,
  status text default 'processing',  -- 'processing' | 'ready' | 'error'
  created_at timestamptz default now()
);

-- ============================================================
-- Document chunks (cho RAG / pgvector)
-- ============================================================
create table if not exists document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  chunk_text text not null,
  embedding vector(768),  -- Gemini text-embedding-004 = 768 dims
  chunk_index int
);

-- Index pgvector để search cosine similarity nhanh
create index if not exists idx_document_chunks_embedding
  on document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- ============================================================
-- Quiz sets
-- ============================================================
create table if not exists quiz_sets (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  title text,
  difficulty text default 'medium',  -- 'easy' | 'medium' | 'hard'
  num_questions int,
  is_shared boolean default false,
  created_at timestamptz default now()
);

-- ============================================================
-- Questions
-- ============================================================
create table if not exists questions (
  id uuid primary key default gen_random_uuid(),
  quiz_set_id uuid references quiz_sets(id) on delete cascade,
  question_text text not null,
  options jsonb not null,  -- {"A": "...", "B": "...", "C": "...", "D": "..."}
  correct_answer text not null  -- "A" | "B" | "C" | "D"
);

-- ============================================================
-- Flashcards
-- ============================================================
create table if not exists flashcards (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  front_text text not null,
  back_text text not null,
  created_at timestamptz default now()
);

-- ============================================================
-- Submissions (lịch sử làm bài)
-- ============================================================
create table if not exists submissions (
  id uuid primary key default gen_random_uuid(),
  quiz_set_id uuid references quiz_sets(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  score float,
  total_questions int,
  correct_count int,
  submitted_at timestamptz default now()
);

-- ============================================================
-- User answers (từng câu trả lời)
-- ============================================================
create table if not exists user_answers (
  id uuid primary key default gen_random_uuid(),
  submission_id uuid references submissions(id) on delete cascade,
  question_id uuid references questions(id) on delete cascade,
  selected_answer text,
  is_correct boolean,
  ai_explanation text  -- giải thích "tại sao sai" từ Gemini
);

-- ============================================================
-- RPC FUNCTION: Similarity search (pgvector)
-- Dùng để RAG giải thích lỗi sai
-- ============================================================
create or replace function match_document_chunks (
  query_embedding vector(768),
  filter_document_id uuid,
  match_count int default 3
)
returns table (
  id uuid,
  document_id uuid,
  chunk_text text,
  similarity float
)
language sql
as $$
  select
    dc.id,
    dc.document_id,
    dc.chunk_text,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  where dc.document_id = filter_document_id
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;
