-- processed.investigation_queue: Everything a person should review, with a reason
-- Source: 01-data/03-processed/investigation-queue.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.investigation_queue (
    dataset           TEXT          NOT NULL,
    source_record_id  TEXT          NOT NULL,
    business_id       TEXT          NOT NULL,
    reason            TEXT          NOT NULL,
    detail            TEXT          NOT NULL,
    CONSTRAINT pk_investigation_queue
        PRIMARY KEY (dataset, source_record_id, reason),
    CONSTRAINT fk_investigation_queue_business
        FOREIGN KEY (business_id) REFERENCES processed.business_profiles (business_id),
    CONSTRAINT ck_investigation_queue_dataset
        CHECK (dataset IN ('bank_transactions', 'business_profiles', 'invoices', 'supplier_bills')),
    CONSTRAINT ck_investigation_queue_reason
        CHECK (reason IN ('amount_conflict', 'bank_row_without_ledger_record', 'conflicting_profile_version', 'missing_payment_date', 'no_bank_record', 'payment_reversed', 'possible_sign_error_in_bank', 'possible_sign_inconsistency', 'unpaired_reversal'))
);

COMMENT ON TABLE processed.investigation_queue IS 'Review queue produced by the pipeline. Polymorphic by design: (dataset, source_record_id) points at a row in the matching table. Workflow columns (owner, resolution) will be added by a later migration.';
COMMENT ON COLUMN processed.investigation_queue.dataset IS 'Table the item lives in: bank_transactions, business_profiles, invoices or supplier_bills.';
COMMENT ON COLUMN processed.investigation_queue.source_record_id IS 'source_record_id of the item within that table (a profile''s conflicting version for business_profiles).';
COMMENT ON COLUMN processed.investigation_queue.business_id IS 'SME the item belongs to.';
COMMENT ON COLUMN processed.investigation_queue.reason IS 'Why it needs review.';
COMMENT ON COLUMN processed.investigation_queue.detail IS 'Human-readable detail: amounts, candidate bank row, description.';
