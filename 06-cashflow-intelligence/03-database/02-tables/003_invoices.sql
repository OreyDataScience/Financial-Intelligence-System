-- processed.invoices: Deduplicated customer invoices with bank reconciliation
-- Source: 01-data/03-processed/invoices_processed.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.invoices (
    source_record_id               TEXT          NOT NULL,
    business_id                    TEXT          NOT NULL,
    invoice_id                     TEXT          NOT NULL,
    customer_id                    TEXT          NOT NULL,
    invoice_date                   TEXT          NOT NULL,
    due_date                       TEXT,
    invoice_amount                 NUMERIC(18,2) NOT NULL,
    amount_paid                    NUMERIC(18,2) NOT NULL,
    invoice_status                 TEXT          NOT NULL,
    payment_date                   TEXT,
    currency                       TEXT          NOT NULL,
    source_file                    TEXT          NOT NULL,
    invoice_date_std               DATE          NOT NULL,
    due_date_std                   DATE,
    payment_date_std               DATE,
    missing_due_date               BOOLEAN       NOT NULL,
    invoice_status_standardized    TEXT          NOT NULL,
    paid_amount_mismatch           BOOLEAN       NOT NULL,
    payment_before_invoice_flag    BOOLEAN       NOT NULL,
    is_duplicate                   BOOLEAN       NOT NULL,
    reconciliation_status          TEXT          NOT NULL,
    reconciliation_reason          TEXT          NOT NULL,
    matched_bank_source_record_id  TEXT,
    match_confidence               TEXT,
    matched_bank_amount            NUMERIC(18,2),
    amount_difference              NUMERIC(18,2),
    CONSTRAINT pk_invoices
        PRIMARY KEY (source_record_id),
    CONSTRAINT uq_invoices_business_invoice_id
        UNIQUE (business_id, invoice_id),
    CONSTRAINT uq_invoices_matched_bank_row
        UNIQUE (matched_bank_source_record_id),
    CONSTRAINT fk_invoices_business
        FOREIGN KEY (business_id) REFERENCES processed.business_profiles (business_id),
    CONSTRAINT fk_invoices_matched_bank_row
        FOREIGN KEY (matched_bank_source_record_id) REFERENCES processed.bank_transactions (source_record_id),
    CONSTRAINT ck_invoices_currency
        CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT ck_invoices_status_standardized
        CHECK (invoice_status_standardized IN ('paid', 'partially_paid', 'unpaid', 'overdue')),
    CONSTRAINT ck_invoices_not_duplicate
        CHECK (NOT is_duplicate),
    CONSTRAINT ck_invoices_due_date_pair
        CHECK ((due_date IS NULL) = (due_date_std IS NULL)),
    CONSTRAINT ck_invoices_payment_date_pair
        CHECK ((payment_date IS NULL) = (payment_date_std IS NULL)),
    CONSTRAINT ck_invoices_missing_flag
        CHECK (missing_due_date = (due_date IS NULL)),
    CONSTRAINT ck_invoices_status_reason_pairing
        CHECK (
          (reconciliation_status = 'matched'
              AND reconciliation_reason IN ('matched_amount_date', 'matched_amount_date_counterparty'))
          OR (reconciliation_status = 'not_applicable' AND reconciliation_reason = 'not_yet_paid')
          OR (reconciliation_status = 'needs_investigation'
              AND reconciliation_reason IN ('no_bank_record', 'amount_conflict',
                  'possible_sign_error_in_bank', 'payment_reversed', 'missing_payment_date'))
      ),
    CONSTRAINT ck_invoices_bank_link_vs_reason
        CHECK ((reconciliation_reason IN ('no_bank_record', 'not_yet_paid', 'missing_payment_date')) = (matched_bank_source_record_id IS NULL)),
    CONSTRAINT ck_invoices_bank_link_columns_together
        CHECK ((matched_bank_source_record_id IS NULL) = (match_confidence IS NULL)
          AND (matched_bank_source_record_id IS NULL) = (matched_bank_amount IS NULL)
          AND (matched_bank_source_record_id IS NULL) = (amount_difference IS NULL)),
    CONSTRAINT ck_invoices_match_confidence
        CHECK (match_confidence IN ('high', 'low')),
    CONSTRAINT ck_invoices_no_blank_strings
        CHECK (COALESCE(due_date, 'x') <> '' AND COALESCE(payment_date, 'x') <> '' AND COALESCE(matched_bank_source_record_id, 'x') <> '' AND COALESCE(match_confidence, 'x') <> '')
);

COMMENT ON TABLE processed.invoices IS 'Customer invoices after duplicate removal, each reconciled to the bank. needs_investigation rows are kept and explained, never dropped.';
COMMENT ON COLUMN processed.invoices.source_record_id IS 'Traceable ID of the imported invoice row. Primary key.';
COMMENT ON COLUMN processed.invoices.business_id IS 'SME this record belongs to.';
COMMENT ON COLUMN processed.invoices.invoice_id IS 'Invoice identifier as issued by the source system. Unique per business after duplicate removal.';
COMMENT ON COLUMN processed.invoices.customer_id IS 'Customer identifier.';
COMMENT ON COLUMN processed.invoices.invoice_date IS 'Date exactly as received (mixed formats). Use the _std column for analysis.';
COMMENT ON COLUMN processed.invoices.due_date IS 'Due date exactly as received. NULL = not supplied.';
COMMENT ON COLUMN processed.invoices.invoice_amount IS 'Original invoice amount in ZAR.';
COMMENT ON COLUMN processed.invoices.amount_paid IS 'Amount the ledger records as paid. 0 is a real zero (nothing paid yet); it is never used for ''unknown''.';
COMMENT ON COLUMN processed.invoices.invoice_status IS 'Source-reported status exactly as received. A claim, not a fact; see the standardized column.';
COMMENT ON COLUMN processed.invoices.payment_date IS 'Payment date exactly as received. NULL = no payment recorded.';
COMMENT ON COLUMN processed.invoices.currency IS 'ISO 4217 currency code. ZAR expected; anything else must be handled explicitly.';
COMMENT ON COLUMN processed.invoices.source_file IS 'Originating accounting export.';
COMMENT ON COLUMN processed.invoices.invoice_date_std IS 'Standardized invoice_date.';
COMMENT ON COLUMN processed.invoices.due_date_std IS 'Standardized due date. NULL when due_date is NULL.';
COMMENT ON COLUMN processed.invoices.payment_date_std IS 'Standardized payment date. NULL when payment_date is NULL.';
COMMENT ON COLUMN processed.invoices.missing_due_date IS 'TRUE when the source did not supply a due date.';
COMMENT ON COLUMN processed.invoices.invoice_status_standardized IS 'Standardized status: paid, partially_paid, unpaid or overdue.';
COMMENT ON COLUMN processed.invoices.paid_amount_mismatch IS 'TRUE when status is paid but amount_paid differs from the invoice amount by more than 1%.';
COMMENT ON COLUMN processed.invoices.payment_before_invoice_flag IS 'TRUE when the recorded payment date is earlier than the invoice date (flagged, not rejected).';
COMMENT ON COLUMN processed.invoices.is_duplicate IS 'Always FALSE in this layer; duplicate imports are removed and logged in duplicates_removed.';
COMMENT ON COLUMN processed.invoices.reconciliation_status IS 'matched, needs_investigation or not_applicable.';
COMMENT ON COLUMN processed.invoices.reconciliation_reason IS 'Why the status was assigned; see the status/reason pairing constraint.';
COMMENT ON COLUMN processed.invoices.matched_bank_source_record_id IS 'Bank row matched to this record, or the best candidate for amount_conflict / sign-error / reversed cases. NULL when no candidate exists.';
COMMENT ON COLUMN processed.invoices.match_confidence IS 'high = counterparty found in the bank description; low = amount and date only. NULL when there is no bank candidate.';
COMMENT ON COLUMN processed.invoices.matched_bank_amount IS 'Absolute amount of the matched / candidate bank row.';
COMMENT ON COLUMN processed.invoices.amount_difference IS 'amount_paid minus matched_bank_amount, in ZAR. Non-zero values mean ledger and bank disagree.';
