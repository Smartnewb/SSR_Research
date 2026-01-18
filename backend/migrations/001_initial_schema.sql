-- SSR Market Research Tool - Initial PostgreSQL Schema
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/mzgjryqodqzhqwppdjvg/sql

-- Workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    current_step INTEGER NOT NULL,
    product_json TEXT,
    core_persona_json TEXT,
    concepts_json TEXT,
    archetypes_json TEXT,
    use_multi_archetype BOOLEAN DEFAULT FALSE,
    currency TEXT DEFAULT 'KRW',
    sample_size INTEGER,
    persona_generation_job_id TEXT,
    survey_execution_job_id TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

-- Generation jobs table
CREATE TABLE IF NOT EXISTS generation_jobs (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    total_personas INTEGER NOT NULL,
    generated_count INTEGER NOT NULL,
    progress REAL NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    error TEXT
);

-- Generation results table
CREATE TABLE IF NOT EXISTS generation_results (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    total_personas INTEGER NOT NULL,
    distribution_stats_json TEXT NOT NULL,
    personas_json TEXT NOT NULL
);

-- Execution jobs table
CREATE TABLE IF NOT EXISTS execution_jobs (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    total_respondents INTEGER NOT NULL,
    completed_count INTEGER NOT NULL,
    progress REAL NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    error TEXT
);

-- Execution results table
CREATE TABLE IF NOT EXISTS execution_results (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    total_respondents INTEGER NOT NULL,
    execution_time REAL NOT NULL,
    mean_score REAL NOT NULL,
    median_score REAL NOT NULL,
    std_dev REAL NOT NULL,
    score_distribution_json TEXT NOT NULL,
    results_json TEXT NOT NULL,
    comparison_mode TEXT DEFAULT 'single',
    concept_scores_json TEXT,
    comparison_stats_json TEXT,
    quick_insight_json TEXT
);

-- QIE jobs table
CREATE TABLE IF NOT EXISTS qie_jobs (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    progress REAL NOT NULL,
    current_stage TEXT,
    message TEXT,
    total_responses INTEGER NOT NULL,
    processed_count INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    error TEXT
);

-- QIE results table
CREATE TABLE IF NOT EXISTS qie_results (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    tier1_results_json TEXT NOT NULL,
    aggregated_stats_json TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    execution_time REAL NOT NULL,
    tier1_time REAL NOT NULL,
    tier2_time REAL NOT NULL,
    report_data_json TEXT,
    report_generation_time REAL,
    created_at TIMESTAMPTZ NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_workflow_id ON generation_jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_jobs_workflow_id ON execution_jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_qie_jobs_workflow_id ON qie_jobs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_qie_results_workflow_id ON qie_results(workflow_id);
