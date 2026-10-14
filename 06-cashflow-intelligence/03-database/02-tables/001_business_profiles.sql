-- processed.business_profiles: One working profile per SME
-- Source: 01-data/03-processed/business_profiles_processed.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.business_profiles (
    source_record_id             TEXT          NOT NULL,
    business_id                  TEXT          NOT NULL,
    business_name                TEXT          NOT NULL,
    industry                     TEXT          NOT NULL,
    business_start_date          DATE          NOT NULL,
    province                     TEXT          NOT NULL,
    employee_count               INTEGER,
    annual_revenue               TEXT,
    accounting_basis             TEXT,
    financial_year_end           TEXT,
    source_file                  TEXT          NOT NULL,
    missing_employee_count       BOOLEAN       NOT NULL,
    missing_financial_year_end   BOOLEAN       NOT NULL,
    annual_revenue_standardized  NUMERIC(18,2),
    revenue_format_flagged       BOOLEAN       NOT NULL,
    conflicting_profile_version  BOOLEAN       NOT NULL,
    profile_status               TEXT          NOT NULL,
    CONSTRAINT pk_business_profiles
        PRIMARY KEY (business_id),
    CONSTRAINT uq_business_profiles_source_record
        UNIQUE (source_record_id),
    CONSTRAINT ck_business_profiles_employee_count
        CHECK (employee_count >= 0),
    CONSTRAINT ck_business_profiles_missing_employee_flag
        CHECK (missing_employee_count = (employee_count IS NULL)),
    CONSTRAINT ck_business_profiles_missing_fye_flag
        CHECK (missing_financial_year_end = (financial_year_end IS NULL)),
    CONSTRAINT ck_business_profiles_status
        CHECK (profile_status IN ('ok', 'conflict_needs_review')),
    CONSTRAINT ck_business_profiles_status_vs_conflict
        CHECK ((profile_status = 'conflict_needs_review') = conflicting_profile_version),
    CONSTRAINT ck_business_profiles_accounting_basis
        CHECK (accounting_basis IN ('Cash', 'Accrual')),
    CONSTRAINT ck_business_profiles_no_blank_strings
        CHECK (COALESCE(annual_revenue, 'x') <> '' AND COALESCE(accounting_basis, 'x') <> '' AND COALESCE(financial_year_end, 'x') <> '')
);

COMMENT ON TABLE processed.business_profiles IS 'One working profile per business. Where the source supplied conflicting versions, the earliest is used and profile_status is conflict_needs_review (see profile_conflicts). Missing values stay NULL; they are never filled.';
COMMENT ON COLUMN processed.business_profiles.source_record_id IS 'Traceable ID of the imported profile row used as the working record. Unique.';
COMMENT ON COLUMN processed.business_profiles.business_id IS 'SME identifier. Primary key; parent of every other table in this schema.';
COMMENT ON COLUMN processed.business_profiles.business_name IS 'Business name as received.';
COMMENT ON COLUMN processed.business_profiles.industry IS 'Industry label exactly as received. Labels are inconsistent across sources; standardization is future work.';
COMMENT ON COLUMN processed.business_profiles.business_start_date IS 'Date the business was established.';
COMMENT ON COLUMN processed.business_profiles.province IS 'South African province.';
COMMENT ON COLUMN processed.business_profiles.employee_count IS 'Approximate employee count. NULL = not supplied (missing, not zero).';
COMMENT ON COLUMN processed.business_profiles.annual_revenue IS 'Reported annual revenue exactly as received, which may be formatted text such as ''R 3,500,000''. NULL = not supplied.';
COMMENT ON COLUMN processed.business_profiles.accounting_basis IS 'Cash or Accrual, if known. NULL = unknown.';
COMMENT ON COLUMN processed.business_profiles.financial_year_end IS 'Financial year-end month. NULL = not supplied.';
COMMENT ON COLUMN processed.business_profiles.source_file IS 'Originating profile source.';
COMMENT ON COLUMN processed.business_profiles.missing_employee_count IS 'TRUE when employee_count was not supplied.';
COMMENT ON COLUMN processed.business_profiles.missing_financial_year_end IS 'TRUE when financial_year_end was not supplied.';
COMMENT ON COLUMN processed.business_profiles.annual_revenue_standardized IS 'annual_revenue parsed to a number in ZAR. NULL when missing or unparseable.';
COMMENT ON COLUMN processed.business_profiles.revenue_format_flagged IS 'TRUE when annual_revenue arrived as formatted text rather than a plain number.';
COMMENT ON COLUMN processed.business_profiles.conflicting_profile_version IS 'TRUE when the source supplied more than one version of this profile.';
COMMENT ON COLUMN processed.business_profiles.profile_status IS 'ok, or conflict_needs_review when a person must confirm which version is correct.';
