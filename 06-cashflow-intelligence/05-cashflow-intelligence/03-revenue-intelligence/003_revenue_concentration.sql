
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 03 — Revenue Intelligence
-- File: 003_revenue_concentration.sql
--
-- Purpose:
-- Measure customer concentration using invoice amounts.
--
-- Important:
-- This measures invoiced customer concentration, not confirmed
-- collected revenue. Missing customer IDs remain visible.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_revenue_concentration AS

WITH invoice_base AS (
    SELECT
        i.business_id,
        bp.business_name,
        i.currency,
        i.customer_id,
        i.invoice_id,
        i.invoice_date_std AS invoice_date,
        DATE_TRUNC('month', i.invoice_date_std)::date AS month_start,
        i.invoice_amount,
        i.is_duplicate,
        i.paid_amount_mismatch,
        i.reconciliation_status,

        CASE
            WHEN i.customer_id IS NULL
              OR BTRIM(i.customer_id) = ''
            THEN TRUE
            ELSE FALSE
        END AS customer_identity_missing

    FROM processed.invoices i

    LEFT JOIN processed.business_profiles bp
        ON bp.business_id = i.business_id

    WHERE i.invoice_date_std IS NOT NULL
),

customer_period AS (
    SELECT
        business_id,
        business_name,
        currency,
        month_start,
        customer_id,

        COUNT(*) AS invoice_record_count,
        COUNT(DISTINCT invoice_id) AS distinct_invoice_count,

        SUM(invoice_amount) AS customer_invoiced_amount,

        COUNT(*) FILTER (
            WHERE is_duplicate = TRUE
        ) AS duplicate_flagged_count,

        COUNT(*) FILTER (
            WHERE paid_amount_mismatch = TRUE
        ) AS payment_mismatch_count,

        COUNT(*) FILTER (
            WHERE reconciliation_status = 'ledger_conflict'
        ) AS ledger_conflict_count,

        BOOL_OR(customer_identity_missing)
            AS customer_identity_missing

    FROM invoice_base
    GROUP BY
        business_id,
        business_name,
        currency,
        month_start,
        customer_id
),

customer_shares AS (
    SELECT
        *,

        SUM(customer_invoiced_amount) OVER (
            PARTITION BY business_id, currency, month_start
        ) AS monthly_invoiced_total,

        COUNT(*) OVER (
            PARTITION BY business_id, currency, month_start
        ) AS customer_groups_in_month,

        CASE
            WHEN SUM(customer_invoiced_amount) OVER (
                PARTITION BY business_id, currency, month_start
            ) > 0
            THEN customer_invoiced_amount
                / SUM(customer_invoiced_amount) OVER (
                    PARTITION BY business_id, currency, month_start
                )
            ELSE NULL
        END AS customer_invoice_share

    FROM customer_period
),

ranked_customers AS (
    SELECT
        *,

        ROW_NUMBER() OVER (
            PARTITION BY business_id, currency, month_start
            ORDER BY customer_invoiced_amount DESC NULLS LAST,
                     customer_id NULLS LAST
        ) AS customer_rank

    FROM customer_shares
),

monthly_concentration AS (
    SELECT
        business_id,
        business_name,
        currency,
        month_start,

        MAX(monthly_invoiced_total) AS monthly_invoiced_total,

        COUNT(*) FILTER (
            WHERE NOT customer_identity_missing
        ) AS identified_customer_groups,

        COUNT(*) FILTER (
            WHERE customer_identity_missing
        ) AS unidentified_customer_groups,

        MAX(customer_groups_in_month)
            AS customer_groups_in_month,

        MAX(customer_invoiced_amount) FILTER (
            WHERE customer_rank = 1
        ) AS top_customer_invoiced_amount,

        MAX(customer_invoice_share) FILTER (
            WHERE customer_rank = 1
        ) AS top_customer_share,

        SUM(customer_invoice_share * customer_invoice_share)
            FILTER (
                WHERE NOT customer_identity_missing
            ) AS identified_customer_hhi,

        SUM(customer_invoiced_amount) FILTER (
            WHERE NOT customer_identity_missing
        ) AS identified_customer_invoiced_amount,

        SUM(customer_invoiced_amount) FILTER (
            WHERE customer_identity_missing
        ) AS unidentified_customer_invoiced_amount,

        SUM(customer_invoice_share) FILTER (
            WHERE customer_rank <= 3
              AND NOT customer_identity_missing
        ) AS top_3_identified_customer_share,

        SUM(duplicate_flagged_count)
            AS duplicate_flagged_count,

        SUM(payment_mismatch_count)
            AS payment_mismatch_count,

        SUM(ledger_conflict_count)
            AS ledger_conflict_count

    FROM ranked_customers
    GROUP BY
        business_id,
        business_name,
        currency,
        month_start
)

SELECT
    business_id,
    business_name,
    currency,
    month_start,

    monthly_invoiced_total,

    identified_customer_groups,
    unidentified_customer_groups,
    customer_groups_in_month,

    top_customer_invoiced_amount,

    ROUND(
        100.0 * top_customer_share,
        2
    ) AS top_customer_share_pct,

    ROUND(
        100.0 * top_3_identified_customer_share,
        2
    ) AS top_3_identified_customer_share_pct,

    ROUND(
        10000.0 * identified_customer_hhi,
        2
    ) AS identified_customer_hhi_10000_scale,

    identified_customer_invoiced_amount,
    unidentified_customer_invoiced_amount,

    duplicate_flagged_count,
    payment_mismatch_count,
    ledger_conflict_count,

    CASE
        WHEN monthly_invoiced_total IS NULL
          OR monthly_invoiced_total <= 0
            THEN 'concentration_not_calculable'
        WHEN unidentified_customer_groups > 0
            THEN 'concentration_incomplete_customer_identity'
        ELSE 'concentration_calculable_from_invoice_records'
    END AS concentration_data_status,

    CURRENT_TIMESTAMP AS view_generated_at

FROM monthly_concentration;
