
-- ============================================================
-- Orey Analytics
-- Phase 06 — Cash Flow Intelligence
-- Module 04: Expense Intelligence
-- Script 003: Supplier Concentration
--
-- Purpose:
-- Measure monthly supplier-bill concentration by business.
--
-- HHI:
-- Sum of squared supplier shares, on a 0-10,000 scale.
-- Calculated only from identifiable suppliers and positive
-- bill amounts, excluding duplicate-flagged records.
--
-- Important:
-- This measures recorded supplier-bill concentration, not
-- verified accounting expenses or bank payments.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_supplier_concentration AS

WITH supplier_monthly AS (
    SELECT
        b.business_id,
        bp.business_name,
        b.currency,
        DATE_TRUNC('month', b.bill_date_std)::date AS month_start,

        b.supplier_id,

        SUM(b.bill_amount) AS supplier_bill_amount,
        COUNT(*) AS supplier_bill_count

    FROM processed.supplier_bills AS b

    LEFT JOIN processed.business_profiles AS bp
        ON bp.business_id = b.business_id

    WHERE b.bill_date_std IS NOT NULL
      AND COALESCE(b.is_duplicate, FALSE) = FALSE

    GROUP BY
        b.business_id,
        bp.business_name,
        b.currency,
        DATE_TRUNC('month', b.bill_date_std)::date,
        b.supplier_id
),

monthly_totals AS (
    SELECT
        business_id,
        business_name,
        currency,
        month_start,

        SUM(supplier_bill_amount) AS total_non_duplicate_bill_amount,

        SUM(supplier_bill_amount) FILTER (
            WHERE supplier_id IS NOT NULL
              AND supplier_bill_amount > 0
        ) AS identifiable_positive_supplier_bill_amount,

        COUNT(*) FILTER (
            WHERE supplier_id IS NOT NULL
        ) AS identifiable_supplier_count,

        COUNT(*) FILTER (
            WHERE supplier_id IS NULL
        ) AS missing_supplier_group_count,

        SUM(supplier_bill_count) FILTER (
            WHERE supplier_id IS NULL
        ) AS bills_with_missing_supplier_id

    FROM supplier_monthly

    GROUP BY
        business_id,
        business_name,
        currency,
        month_start
),

positive_supplier_shares AS (
    SELECT
        s.business_id,
        s.currency,
        s.month_start,
        s.supplier_id,
        s.supplier_bill_amount,

        t.identifiable_positive_supplier_bill_amount,

        s.supplier_bill_amount
            / NULLIF(
                t.identifiable_positive_supplier_bill_amount,
                0
            ) AS supplier_share

    FROM supplier_monthly AS s

    INNER JOIN monthly_totals AS t
        ON t.business_id = s.business_id
       AND t.currency IS NOT DISTINCT FROM s.currency
       AND t.month_start = s.month_start

    WHERE s.supplier_id IS NOT NULL
      AND s.supplier_bill_amount > 0
),

concentration AS (
    SELECT
        business_id,
        currency,
        month_start,

        COUNT(*) AS positive_supplier_count,

        MAX(supplier_share) * 100
            AS largest_supplier_share_pct,

        SUM(supplier_share * supplier_share) * 10000
            AS supplier_concentration_hhi

    FROM positive_supplier_shares

    GROUP BY
        business_id,
        currency,
        month_start
)

SELECT
    t.business_id,
    t.business_name,
    t.currency,
    t.month_start,

    t.total_non_duplicate_bill_amount,
    t.identifiable_positive_supplier_bill_amount,

    t.identifiable_supplier_count,
    t.missing_supplier_group_count,
    COALESCE(t.bills_with_missing_supplier_id, 0)
        AS bills_with_missing_supplier_id,

    COALESCE(c.positive_supplier_count, 0)
        AS positive_supplier_count,

    c.largest_supplier_share_pct,
    c.supplier_concentration_hhi,

    CASE
        WHEN c.supplier_concentration_hhi IS NULL
            THEN 'Not calculable'
        WHEN c.supplier_concentration_hhi < 1500
            THEN 'Lower concentration'
        WHEN c.supplier_concentration_hhi < 2500
            THEN 'Moderate concentration'
        ELSE 'Higher concentration'
    END AS supplier_concentration_band,

    CASE
        WHEN t.total_non_duplicate_bill_amount IS NULL
          OR t.total_non_duplicate_bill_amount <= 0
            THEN TRUE
        ELSE FALSE
    END AS total_bill_amount_non_positive_or_missing,

    CASE
        WHEN COALESCE(t.bills_with_missing_supplier_id, 0) > 0
            THEN TRUE
        ELSE FALSE
    END AS supplier_identity_incomplete,

    FALSE AS accounting_expenses_verified,
    FALSE AS bank_outflows_verified,

    CURRENT_TIMESTAMP AS view_generated_at

FROM monthly_totals AS t

LEFT JOIN concentration AS c
    ON c.business_id = t.business_id
   AND c.currency IS NOT DISTINCT FROM t.currency
   AND c.month_start = t.month_start;
