-- processed.data_quality_metrics: Per-business data-quality and reconciliation metrics
-- Source: 01-data/03-processed/data-quality-metrics.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.data_quality_metrics (
    business_id  TEXT          NOT NULL,
    dataset      TEXT          NOT NULL,
    metric       TEXT          NOT NULL,
    value        NUMERIC(18,4),
    CONSTRAINT pk_data_quality_metrics
        PRIMARY KEY (business_id, dataset, metric),
    CONSTRAINT fk_data_quality_metrics_business
        FOREIGN KEY (business_id) REFERENCES processed.business_profiles (business_id),
    CONSTRAINT ck_data_quality_metrics_dataset
        CHECK (dataset IN ('bank_transactions', 'invoices', 'supplier_bills'))
);

COMMENT ON TABLE processed.data_quality_metrics IS 'Long-format metrics (one row per business, dataset and metric): rows received, duplicate / missing / delay rates, and reconciliation match rates. Produced by the pipeline from staging data only.';
COMMENT ON COLUMN processed.data_quality_metrics.business_id IS 'SME the metric describes.';
COMMENT ON COLUMN processed.data_quality_metrics.dataset IS 'bank_transactions, invoices or supplier_bills.';
COMMENT ON COLUMN processed.data_quality_metrics.metric IS 'Metric name, e.g. duplicate_rate, match_rate, rows_received.';
COMMENT ON COLUMN processed.data_quality_metrics.value IS 'Metric value. Rates are fractions between 0 and 1; counts are whole numbers. NULL = undefined (for example a match rate with nothing to reconcile).';
