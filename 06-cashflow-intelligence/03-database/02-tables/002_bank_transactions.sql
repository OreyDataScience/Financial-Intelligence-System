-- processed.bank_transactions: Deduplicated bank transactions with reconciliation outcome
-- Source: 01-data/03-processed/bank_transactions_processed.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.bank_transactions (
    source_record_id                   TEXT          NOT NULL,
    business_id                        TEXT          NOT NULL,
    bank_name                          TEXT          NOT NULL,
    account_id                         TEXT          NOT NULL,
    transaction_date                   TEXT          NOT NULL,
    posting_date                       TEXT          NOT NULL,
    transaction_description            TEXT          NOT NULL,
    transaction_reference              TEXT,
    debit_amount                       NUMERIC(18,2),
    credit_amount                      NUMERIC(18,2),
    balance_after_transaction          NUMERIC(18,2),
    currency                           TEXT          NOT NULL,
    source_file                        TEXT          NOT NULL,
    transaction_date_std               DATE          NOT NULL,
    posting_date_std                   DATE          NOT NULL,
    missing_transaction_reference      BOOLEAN       NOT NULL,
    missing_balance_after_transaction  BOOLEAN       NOT NULL,
    net_amount                         NUMERIC(18,2) NOT NULL,
    posting_delay_days                 INTEGER       NOT NULL,
    delayed_posting_flag               BOOLEAN       NOT NULL,
    description_normalized             TEXT          NOT NULL,
    is_reversal                        BOOLEAN       NOT NULL,
    possible_sign_inconsistency        BOOLEAN       NOT NULL,
    is_duplicate                       BOOLEAN       NOT NULL,
    duplicate_group_size               INTEGER       NOT NULL,
    is_operational                     BOOLEAN       NOT NULL,
    netted_pair_id                     TEXT,
    is_netted_pair                     BOOLEAN       NOT NULL,
    review_reasons                     TEXT,
    data_quality_notes                 TEXT,
    reconciliation_status              TEXT          NOT NULL,
    matched_ledger_type                TEXT,
    matched_ledger_source_record_id    TEXT,
    CONSTRAINT pk_bank_transactions
        PRIMARY KEY (source_record_id),
    CONSTRAINT uq_bank_transactions_ledger_link
        UNIQUE (matched_ledger_type, matched_ledger_source_record_id),
    CONSTRAINT fk_bank_transactions_business
        FOREIGN KEY (business_id) REFERENCES processed.business_profiles (business_id),
    CONSTRAINT ck_bank_transactions_currency
        CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT ck_bank_transactions_net_amount_identity
        CHECK (net_amount = COALESCE(credit_amount, 0) - COALESCE(debit_amount, 0)),
    CONSTRAINT ck_bank_transactions_missing_reference_flag
        CHECK (missing_transaction_reference = (transaction_reference IS NULL)),
    CONSTRAINT ck_bank_transactions_missing_balance_flag
        CHECK (missing_balance_after_transaction = (balance_after_transaction IS NULL)),
    CONSTRAINT ck_bank_transactions_not_duplicate
        CHECK (NOT is_duplicate),
    CONSTRAINT ck_bank_transactions_duplicate_group_size
        CHECK (duplicate_group_size >= 1),
    CONSTRAINT ck_bank_transactions_pair_flag
        CHECK (is_netted_pair = (netted_pair_id IS NOT NULL)),
    CONSTRAINT ck_bank_transactions_review_reasons
        CHECK (review_reasons IN ('possible_sign_inconsistency', 'unpaired_reversal')),
    CONSTRAINT ck_bank_transactions_reconciliation_status
        CHECK (reconciliation_status IN ('matched_ledger', 'ledger_conflict', 'operational_no_ledger_expected', 'reversal', 'unmatched_needs_investigation')),
    CONSTRAINT ck_bank_transactions_ledger_type
        CHECK (matched_ledger_type IN ('invoice', 'supplier_bill')),
    CONSTRAINT ck_bank_transactions_ledger_link_together
        CHECK ((matched_ledger_type IS NULL) = (matched_ledger_source_record_id IS NULL)),
    CONSTRAINT ck_bank_transactions_status_vs_ledger_link
        CHECK ((reconciliation_status IN ('matched_ledger', 'ledger_conflict')) = (matched_ledger_type IS NOT NULL)),
    CONSTRAINT ck_bank_transactions_no_blank_strings
        CHECK (COALESCE(transaction_reference, 'x') <> '' AND COALESCE(netted_pair_id, 'x') <> '' AND COALESCE(review_reasons, 'x') <> '' AND COALESCE(data_quality_notes, 'x') <> '' AND COALESCE(matched_ledger_type, 'x') <> '' AND COALESCE(matched_ledger_source_record_id, 'x') <> '')
);

COMMENT ON TABLE processed.bank_transactions IS 'Bank transactions after duplicate removal. Raw fields are kept exactly as received; standardized columns and flags sit beside them. Reversal pairs are linked, not dropped. Nothing is ''fixed'': suspect rows carry review_reasons.';
COMMENT ON COLUMN processed.bank_transactions.source_record_id IS 'Traceable ID of the imported bank row. Primary key.';
COMMENT ON COLUMN processed.bank_transactions.business_id IS 'SME that owns the account.';
COMMENT ON COLUMN processed.bank_transactions.bank_name IS 'Financial institution.';
COMMENT ON COLUMN processed.bank_transactions.account_id IS 'Bank account identifier.';
COMMENT ON COLUMN processed.bank_transactions.transaction_date IS 'Transaction date exactly as received (mixed formats). Use transaction_date_std for analysis.';
COMMENT ON COLUMN processed.bank_transactions.posting_date IS 'Posting date exactly as received (mixed formats). Use posting_date_std for analysis.';
COMMENT ON COLUMN processed.bank_transactions.transaction_description IS 'Bank-provided description exactly as received.';
COMMENT ON COLUMN processed.bank_transactions.transaction_reference IS 'Bank reference. NULL = not supplied (flagged in missing_transaction_reference).';
COMMENT ON COLUMN processed.bank_transactions.debit_amount IS 'Debit as supplied, in ZAR. NULL = not supplied on this row (not zero).';
COMMENT ON COLUMN processed.bank_transactions.credit_amount IS 'Credit as supplied, in ZAR. NULL = not supplied on this row (not zero).';
COMMENT ON COLUMN processed.bank_transactions.balance_after_transaction IS 'Reported running balance. NULL = not supplied (flagged in missing_balance_after_transaction).';
COMMENT ON COLUMN processed.bank_transactions.currency IS 'ISO 4217 currency code. ZAR expected; anything else must be handled explicitly.';
COMMENT ON COLUMN processed.bank_transactions.source_file IS 'Originating statement / export file.';
COMMENT ON COLUMN processed.bank_transactions.transaction_date_std IS 'Standardized transaction date.';
COMMENT ON COLUMN processed.bank_transactions.posting_date_std IS 'Standardized posting date.';
COMMENT ON COLUMN processed.bank_transactions.missing_transaction_reference IS 'TRUE when no bank reference was supplied.';
COMMENT ON COLUMN processed.bank_transactions.missing_balance_after_transaction IS 'TRUE when no running balance was supplied.';
COMMENT ON COLUMN processed.bank_transactions.net_amount IS 'Signed amount derived from the source columns: credit minus debit. Positive = money in, negative = money out.';
COMMENT ON COLUMN processed.bank_transactions.posting_delay_days IS 'Days between posting date and transaction date.';
COMMENT ON COLUMN processed.bank_transactions.delayed_posting_flag IS 'TRUE when posting was delayed by 7 or more days.';
COMMENT ON COLUMN processed.bank_transactions.description_normalized IS 'Upper-cased description with punctuation and spacing normalized; used for matching.';
COMMENT ON COLUMN processed.bank_transactions.is_reversal IS 'TRUE when the row reverses an earlier transaction.';
COMMENT ON COLUMN processed.bank_transactions.possible_sign_inconsistency IS 'TRUE when an outflow-style description is recorded as a credit. A heuristic, so it is flagged and routed to review, never auto-corrected.';
COMMENT ON COLUMN processed.bank_transactions.is_duplicate IS 'Always FALSE in this layer; duplicate imports are removed and logged in duplicates_removed.';
COMMENT ON COLUMN processed.bank_transactions.duplicate_group_size IS 'Size of the duplicate group this row came from, before removal. 2 = one duplicate import was removed.';
COMMENT ON COLUMN processed.bank_transactions.is_operational IS 'TRUE for rows that never have an invoice or bill counterpart (card settlements, cash-and-carry, payroll, operating expenses).';
COMMENT ON COLUMN processed.bank_transactions.netted_pair_id IS 'Shared ID linking a transaction to its reversal. NULL = not part of a reversal pair.';
COMMENT ON COLUMN processed.bank_transactions.is_netted_pair IS 'TRUE when the row belongs to a reversal pair.';
COMMENT ON COLUMN processed.bank_transactions.review_reasons IS 'Why a person should review this row. NULL = nothing to review.';
COMMENT ON COLUMN processed.bank_transactions.data_quality_notes IS 'Informational notes (missing reference, missing balance, delayed posting), semicolon separated. NULL = none.';
COMMENT ON COLUMN processed.bank_transactions.reconciliation_status IS 'matched_ledger, ledger_conflict, operational_no_ledger_expected, reversal or unmatched_needs_investigation.';
COMMENT ON COLUMN processed.bank_transactions.matched_ledger_type IS 'invoice or supplier_bill when linked to a ledger record. NULL = no link.';
COMMENT ON COLUMN processed.bank_transactions.matched_ledger_source_record_id IS 'source_record_id of the linked invoice or bill (polymorphic: see matched_ledger_type). NULL = no link.';
