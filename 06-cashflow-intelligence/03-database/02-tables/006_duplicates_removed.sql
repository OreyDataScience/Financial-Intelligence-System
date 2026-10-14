-- processed.duplicates_removed: Audit trail of removed duplicate imports
-- Source: 01-data/03-processed/duplicates-removed.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.duplicates_removed (
    dataset           TEXT          NOT NULL,
    source_record_id  TEXT          NOT NULL,
    business_id       TEXT          NOT NULL,
    CONSTRAINT pk_duplicates_removed
        PRIMARY KEY (dataset, source_record_id),
    CONSTRAINT fk_duplicates_removed_business
        FOREIGN KEY (business_id) REFERENCES processed.business_profiles (business_id),
    CONSTRAINT ck_duplicates_removed_dataset
        CHECK (dataset IN ('bank_transactions', 'invoices', 'supplier_bills'))
);

COMMENT ON TABLE processed.duplicates_removed IS 'Rows removed from the analysis layer as duplicate imports. Kept so nothing is ever silently lost.';
COMMENT ON COLUMN processed.duplicates_removed.dataset IS 'Table the duplicate came from: bank_transactions, invoices or supplier_bills.';
COMMENT ON COLUMN processed.duplicates_removed.source_record_id IS 'source_record_id of the removed duplicate import.';
COMMENT ON COLUMN processed.duplicates_removed.business_id IS 'SME the duplicate belonged to.';
