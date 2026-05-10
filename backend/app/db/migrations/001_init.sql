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
  correct_answer text not null,  -- "A" | "B" | "C" | "D"
  difficulty_label text,         -- "easy" | "medium" | "hard"
  difficulty_score float,        -- model confidence
  difficulty_version text        -- model version
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
-- =========
-- mới
-- Enable RLS on tables
alter table users enable row level security;
alter table documents enable row level security;
alter table document_chunks enable row level security;
alter table quiz_sets enable row level security;
alter table questions enable row level security;
alter table flashcards enable row level security;
alter table submissions enable row level security;
alter table user_answers enable row level security;

-- Users: chỉ xem chính mình
create policy "Users can view own profile"
on users for select
using (id = auth.uid());

create policy "Users can update own profile"
on users for update
using (id = auth.uid());

-- Documents
create policy "Documents: owner can read"
on documents for select
using (user_id = auth.uid());

create policy "Documents: owner can insert"
on documents for insert
with check (user_id = auth.uid());

create policy "Documents: owner can update"
on documents for update
using (user_id = auth.uid());

create policy "Documents: owner can delete"
on documents for delete
using (user_id = auth.uid());

-- Document chunks: chỉ chủ tài liệu đọc
create policy "Chunks: owner can read"
on document_chunks for select
using (
  exists (
    select 1 from documents d
    where d.id = document_chunks.document_id
      and d.user_id = auth.uid()
  )
);

-- Quiz sets: chỉ chủ tài liệu
create policy "Quiz sets: owner can read"
on quiz_sets for select
using (
  exists (
    select 1 from documents d
    where d.id = quiz_sets.document_id
      and d.user_id = auth.uid()
  )
);

create policy "Quiz sets: owner can insert"
on quiz_sets for insert
with check (
  exists (
    select 1 from documents d
    where d.id = quiz_sets.document_id
      and d.user_id = auth.uid()
  )
);

create policy "Quiz sets: owner can update"
on quiz_sets for update
using (
  exists (
    select 1 from documents d
    where d.id = quiz_sets.document_id
      and d.user_id = auth.uid()
  )
);

create policy "Quiz sets: owner can delete"
on quiz_sets for delete
using (
  exists (
    select 1 from documents d
    where d.id = quiz_sets.document_id
      and d.user_id = auth.uid()
  )
);

-- Questions: theo quiz_set -> document -> user
create policy "Questions: owner can read"
on questions for select
using (
  exists (
    select 1
    from quiz_sets qs
    join documents d on d.id = qs.document_id
    where qs.id = questions.quiz_set_id
      and d.user_id = auth.uid()
  )
);

create policy "Questions: owner can insert"
on questions for insert
with check (
  exists (
    select 1
    from quiz_sets qs
    join documents d on d.id = qs.document_id
    where qs.id = questions.quiz_set_id
      and d.user_id = auth.uid()
  )
);

create policy "Questions: owner can delete"
on questions for delete
using (
  exists (
    select 1
    from quiz_sets qs
    join documents d on d.id = qs.document_id
    where qs.id = questions.quiz_set_id
      and d.user_id = auth.uid()
  )
);

-- Flashcards: theo document
create policy "Flashcards: owner can read"
on flashcards for select
using (
  exists (
    select 1 from documents d
    where d.id = flashcards.document_id
      and d.user_id = auth.uid()
  )
);

create policy "Flashcards: owner can insert"
on flashcards for insert
with check (
  exists (
    select 1 from documents d
    where d.id = flashcards.document_id
      and d.user_id = auth.uid()
  )
);

create policy "Flashcards: owner can delete"
on flashcards for delete
using (
  exists (
    select 1 from documents d
    where d.id = flashcards.document_id
      and d.user_id = auth.uid()
  )
);

-- Submissions: chỉ user của submission
create policy "Submissions: owner can read"
on submissions for select
using (user_id = auth.uid());

create policy "Submissions: owner can insert"
on submissions for insert
with check (user_id = auth.uid());

-- User answers: theo submission -> user
create policy "User answers: owner can read"
on user_answers for select
using (
  exists (
    select 1 from submissions s
    where s.id = user_answers.submission_id
      and s.user_id = auth.uid()
  )
);

create policy "User answers: owner can insert"
on user_answers for insert
with check (
  exists (
    select 1 from submissions s
    where s.id = user_answers.submission_id
      and s.user_id = auth.uid()
  )
);
-- =====
-- bucket 
-- Only authenticated users can upload/read their own files
create policy "Storage read own files"
on storage.objects for select
using (
  bucket_id = 'documents'
  and auth.uid()::text = (storage.foldername(name))[1]
);

create policy "Storage upload own files"
on storage.objects for insert
with check (
  bucket_id = 'documents'
  and auth.uid()::text = (storage.foldername(name))[1]
);