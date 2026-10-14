-- Schema: processed
-- The analysis-ready layer: deduplicated, reconciled data produced by the Phase 06
-- data pipeline (01-data/03-processed). Everything downstream reads from here.
--
-- One schema per pipeline layer. `processed` comes first because it is what the
-- analytics stages consume. Later phases add their own schemas in their own
-- migrations (analytics, forecasts, scenarios, risk), keeping each stage's outputs
-- separate from the data it reads.

CREATE SCHEMA processed;

COMMENT ON SCHEMA processed IS
    'Analysis-ready SME financial data: deduplicated and reconciled. Produced by the Phase 06 data pipeline; reloaded as a whole, never edited in place.';
