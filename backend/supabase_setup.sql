-- ====================================================
-- AI Study Assistant Portal — Supabase Database Setup
-- Run this in the Supabase SQL Editor (Dashboard > SQL Editor)
-- ====================================================

-- 1. Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    filename TEXT NOT NULL,
    file_path TEXT,
    file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx')),
    file_size BIGINT NOT NULL DEFAULT 0,
    extracted_text TEXT,
    exam_notes JSONB,
    status TEXT NOT NULL DEFAULT 'uploading' CHECK (status IN ('uploading', 'processing', 'ready', 'error')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for efficient user queries
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- Auto-update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS documents_updated_at ON documents;
CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 2. Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_document ON chat_history(document_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id);

-- 3. Disable RLS for now (single-user mode)
-- When adding auth later, enable RLS and create policies:
--   ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
--   CREATE POLICY "Users can manage own documents"
--     ON documents FOR ALL USING (auth.uid() = user_id);
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history DISABLE ROW LEVEL SECURITY;

-- 4. Storage bucket (create via Dashboard > Storage > New Bucket)
-- Bucket name: study-documents
-- Public: No (private bucket)
-- File size limit: 20MB
-- NOTE: Storage buckets must be created via the Supabase Dashboard UI,
-- not via SQL. Create a bucket named "study-documents" with:
--   - Public access: OFF
--   - Max file size: 20971520 (20MB)
