CREATE TABLE ingestion_runs (
    ingestion_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    source_sha256 TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    source_row_count BIGINT,
    inserted_count BIGINT NOT NULL DEFAULT 0,
    updated_count BIGINT NOT NULL DEFAULT 0,
    rejected_count BIGINT NOT NULL DEFAULT 0,
    validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT
);

CREATE TABLE complaints (
    complaint_id BIGINT PRIMARY KEY,
    date_received DATE NOT NULL,
    product TEXT NOT NULL,
    sub_product TEXT,
    issue TEXT NOT NULL,
    sub_issue TEXT,
    company TEXT NOT NULL,
    state TEXT,
    zip_code TEXT,
    tags TEXT,
    submitted_via TEXT,
    date_sent_to_company DATE,
    company_response_to_consumer TEXT,
    company_public_response TEXT,
    timely_response BOOLEAN,
    consumer_consent_provided TEXT,
    consumer_complaint_narrative TEXT,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(ingestion_run_id),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector(
            'english',
            COALESCE(consumer_complaint_narrative, '')
        )
    ) STORED
);

CREATE INDEX idx_complaints_company_received
    ON complaints (company, date_received DESC);

CREATE INDEX idx_complaints_product_issue_state_received
    ON complaints (product, issue, state, date_received DESC);

CREATE INDEX idx_complaints_received
    ON complaints (date_received DESC);

CREATE INDEX idx_complaints_narrative_search
    ON complaints USING GIN (search_vector);