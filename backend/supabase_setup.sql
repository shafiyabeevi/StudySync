-- StudySync additive Supabase migration.
-- Run manually in the Supabase SQL Editor after verifying the existing
-- documents table has UUID id/user_id columns and owner-scoped RLS policies.
-- This does not recreate documents/chat_history or change Storage policies.

BEGIN;

CREATE TABLE IF NOT EXISTS public.teach_it_back_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    topic TEXT,
    student_explanation TEXT NOT NULL,
    ai_feedback JSONB,
    score INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_teach_it_back_user_document_created
    ON public.teach_it_back_attempts (user_id, document_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_teach_it_back_document_topic_created
    ON public.teach_it_back_attempts (document_id, topic, created_at DESC);

ALTER TABLE public.teach_it_back_attempts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.teach_it_back_attempts FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE public.teach_it_back_attempts TO authenticated;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'teach_it_back_attempts'
          AND policyname = 'teach_it_back_select_own'
    ) THEN
        CREATE POLICY teach_it_back_select_own
            ON public.teach_it_back_attempts
            FOR SELECT TO authenticated
            USING (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = teach_it_back_attempts.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'teach_it_back_attempts'
          AND policyname = 'teach_it_back_insert_own'
    ) THEN
        CREATE POLICY teach_it_back_insert_own
            ON public.teach_it_back_attempts
            FOR INSERT TO authenticated
            WITH CHECK (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = teach_it_back_attempts.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'teach_it_back_attempts'
          AND policyname = 'teach_it_back_update_own'
    ) THEN
        CREATE POLICY teach_it_back_update_own
            ON public.teach_it_back_attempts
            FOR UPDATE TO authenticated
            USING (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = teach_it_back_attempts.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            )
            WITH CHECK (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = teach_it_back_attempts.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'teach_it_back_attempts'
          AND policyname = 'teach_it_back_delete_own'
    ) THEN
        CREATE POLICY teach_it_back_delete_own
            ON public.teach_it_back_attempts
            FOR DELETE TO authenticated
            USING (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = teach_it_back_attempts.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;
END
$$;

COMMIT;
