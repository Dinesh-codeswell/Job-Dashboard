-- SQL Script for Supabase/PostgreSQL
-- Run this in your Supabase SQL Editor

-- Create the jobs table
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT UNIQUE, -- ID from the scraper/source
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    company_logo TEXT,
    location TEXT,
    search_city TEXT,
    employment_type TEXT,
    posted_date TEXT,
    date_added TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    job_url TEXT UNIQUE,
    job_description TEXT,
    source TEXT, -- 'linkedin', 'indeed', 'naukri'
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for high-performance searching
CREATE INDEX IF NOT EXISTS idx_jobs_job_title ON public.jobs USING gin (job_title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON public.jobs USING gin (company gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_jobs_search_city ON public.jobs (search_city);
CREATE INDEX IF NOT EXISTS idx_jobs_employment_type ON public.jobs (employment_type);
CREATE INDEX IF NOT EXISTS idx_jobs_date_added ON public.jobs (date_added DESC);

-- Enable full text search on job title and company
ALTER TABLE public.jobs ADD COLUMN IF NOT EXISTS fts_tokens tsvector GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(job_title, '') || ' ' || coalesce(company, '') || ' ' || coalesce(job_description, ''))
) STORED;

CREATE INDEX IF NOT EXISTS idx_jobs_fts ON public.jobs USING gin (fts_tokens);

-- Enable Row Level Security (RLS)
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access
CREATE POLICY "Allow public read access" ON public.jobs
    FOR SELECT USING (true);

-- Create policy to allow service role to manage data
CREATE POLICY "Allow service role to manage data" ON public.jobs
    USING (auth.role() = 'service_role');

-- Install pg_trgm extension for fuzzy searching if not exists
CREATE EXTENSION IF NOT EXISTS pg_trgm;
