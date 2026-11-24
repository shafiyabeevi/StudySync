-- Upgrade Me activity progress. Apply after the existing documents table
-- and teach_it_back_attempts table have been created.

BEGIN;

CREATE TABLE IF NOT EXISTS public.upgrade_me_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    concept_name TEXT NOT NULL,
    concept_description TEXT NOT NULL,
    source_evidence TEXT NOT NULL,
    improvement_status TEXT NOT NULL DEFAULT 'needs_improvement'
        CHECK (improvement_status IN ('needs_improvement', 'practicing', 'improved')),
    last_evaluation_status TEXT
        CHECK (last_evaluation_status IN ('fully_covered', 'partially_covered', 'missed', 'incorrect')),
    activity_progress JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_practiced_at TIMESTAMPTZ,
    last_evaluated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT upgrade_me_progress_concept_unique
        UNIQUE (user_id, document_id, topic, concept_id)
);

CREATE INDEX IF NOT EXISTS idx_upgrade_me_progress_user_document
    ON public.upgrade_me_progress (user_id, document_id, updated_at DESC);

ALTER TABLE public.upgrade_me_progress ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.upgrade_me_progress FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE public.upgrade_me_progress TO authenticated;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'upgrade_me_progress'
          AND policyname = 'upgrade_me_progress_select_own'
    ) THEN
        CREATE POLICY upgrade_me_progress_select_own
            ON public.upgrade_me_progress
            FOR SELECT TO authenticated
            USING (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = upgrade_me_progress.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'upgrade_me_progress'
          AND policyname = 'upgrade_me_progress_insert_own'
    ) THEN
        CREATE POLICY upgrade_me_progress_insert_own
            ON public.upgrade_me_progress
            FOR INSERT TO authenticated
            WITH CHECK (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = upgrade_me_progress.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'upgrade_me_progress'
          AND policyname = 'upgrade_me_progress_update_own'
    ) THEN
        CREATE POLICY upgrade_me_progress_update_own
            ON public.upgrade_me_progress
            FOR UPDATE TO authenticated
            USING (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = upgrade_me_progress.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            )
            WITH CHECK (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = upgrade_me_progress.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'upgrade_me_progress'
          AND policyname = 'upgrade_me_progress_delete_own'
    ) THEN
        CREATE POLICY upgrade_me_progress_delete_own
            ON public.upgrade_me_progress
            FOR DELETE TO authenticated
            USING (
                user_id = (SELECT auth.uid())
                AND EXISTS (
                    SELECT 1 FROM public.documents d
                    WHERE d.id = upgrade_me_progress.document_id
                      AND d.user_id = (SELECT auth.uid())
                )
            );
    END IF;
END
$$;

COMMIT;
