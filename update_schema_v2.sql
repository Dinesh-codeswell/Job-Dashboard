-- Run this in Supabase SQL Editor
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS posted_at_timestamp TIMESTAMP WITH TIME ZONE;
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at_timestamp ON public.jobs (posted_at_timestamp DESC);

-- Cleanup existing data that might be stale
DELETE FROM public.jobs WHERE posted_at_timestamp < NOW() - INTERVAL '3 days';
