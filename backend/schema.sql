CREATE TABLE IF NOT EXISTS companies (
  id SERIAL PRIMARY KEY, name TEXT NOT NULL, website TEXT NOT NULL,
  settings JSONB DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS profile_facts (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  field TEXT NOT NULL, value TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('verified','assumed','founder_provided')),
  evidence_url TEXT, updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS interview_qa (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  seq INT NOT NULL, question TEXT NOT NULL, answer TEXT, skipped BOOLEAN DEFAULT false,
  is_followup BOOLEAN DEFAULT false, updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (category IN ('customers','competitors','market','internal')),
  name TEXT, url TEXT NOT NULL, reason TEXT NOT NULL,
  status TEXT DEFAULT 'suggested' CHECK (status IN ('suggested','approved','removed','dead','inactive')),
  competitor_name TEXT, source_reliability REAL, relevance_score REAL,
  last_checked TIMESTAMPTZ, last_status_code INT, discovered_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (company_id, url)
);
CREATE TABLE IF NOT EXISTS crawl_runs (
  id SERIAL PRIMARY KEY, source_id INT REFERENCES sources(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ DEFAULT now(), status TEXT, http_status INT,
  new_docs INT DEFAULT 0, error TEXT
);
CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY, source_id INT REFERENCES sources(id) ON DELETE CASCADE,
  url TEXT NOT NULL, title TEXT, content TEXT, content_hash TEXT NOT NULL,
  published_at TIMESTAMPTZ, discovered_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (source_id, content_hash)
);
CREATE TABLE IF NOT EXISTS signals (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  document_id INT REFERENCES documents(id) ON DELETE SET NULL,
  category TEXT NOT NULL, competitor_name TEXT,
  what_happened TEXT NOT NULL, evidence_snippet TEXT NOT NULL, source_url TEXT NOT NULL,
  published_at TIMESTAMPTZ, discovered_at TIMESTAMPTZ DEFAULT now(),
  verification_status TEXT CHECK (verification_status IN ('verified','unverified','single_source')),
  why_it_matters TEXT, business_area TEXT,
  impact_type TEXT CHECK (impact_type IN ('opportunity','threat','neutral')),
  urgency TEXT, suggested_action TEXT,
  source_reliability REAL, evidence_strength REAL, strategic_relevance REAL,
  rank_score REAL, rank_explanation TEXT, interpretation TEXT
);
CREATE TABLE IF NOT EXISTS briefs (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  period_start DATE, period_end DATE, content JSONB NOT NULL, html TEXT,
  trigger TEXT DEFAULT 'scheduled', created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS actions (
  id SERIAL PRIMARY KEY, brief_id INT REFERENCES briefs(id) ON DELETE CASCADE,
  title TEXT NOT NULL, reason TEXT, owner TEXT, priority TEXT,
  status TEXT DEFAULT 'open', updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS uploads (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  filename TEXT, kind TEXT, extracted_text TEXT, uploaded_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS job_runs (
  id SERIAL PRIMARY KEY, job_name TEXT NOT NULL, company_id INT,
  status TEXT NOT NULL CHECK (status IN ('running','success','failed')),
  started_at TIMESTAMPTZ DEFAULT now(), finished_at TIMESTAMPTZ, error TEXT, summary JSONB
);
CREATE TABLE IF NOT EXISTS audit_reports (
  id SERIAL PRIMARY KEY, company_id INT REFERENCES companies(id) ON DELETE CASCADE,
  content JSONB NOT NULL, created_at TIMESTAMPTZ DEFAULT now()
);
