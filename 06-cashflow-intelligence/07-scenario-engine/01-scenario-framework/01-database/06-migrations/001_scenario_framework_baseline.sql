--
-- PostgreSQL database dump
--

\restrict B104ndr2xy7coYMxMeEvM3BvuifEXwWyLmVemZAc7nmpQLkDgafbeTgd6JTQm6f

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: scenario; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA scenario;


--
-- Name: enforce_execution_lifecycle(); Type: FUNCTION; Schema: scenario; Owner: -
--

CREATE FUNCTION scenario.enforce_execution_lifecycle() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN

    -- Preserve execution identity.
    IF NEW.execution_id IS DISTINCT FROM OLD.execution_id
       OR NEW.version_id IS DISTINCT FROM OLD.version_id
       OR NEW.business_id IS DISTINCT FROM OLD.business_id
    THEN
        RAISE EXCEPTION
            'Execution identity and ownership cannot be changed.';
    END IF;

    -- Freeze the random seed after execution starts.
    IF OLD.started_at IS NOT NULL
       AND NEW.random_seed IS DISTINCT FROM OLD.random_seed
    THEN
        RAISE EXCEPTION
            'Random seed cannot be changed after execution starts.';
    END IF;

    -- Enforce valid status transitions.
    IF NEW.execution_status IS DISTINCT FROM OLD.execution_status
    THEN
        IF NOT (
            (OLD.execution_status = 'pending'
                AND NEW.execution_status IN ('validating', 'failed'))

            OR

            (OLD.execution_status = 'validating'
                AND NEW.execution_status IN ('running', 'failed'))

            OR

            (OLD.execution_status = 'running'
                AND NEW.execution_status IN (
                    'completed',
                    'completed_with_warnings',
                    'failed'
                ))
        )
        THEN
            RAISE EXCEPTION
                'Invalid execution status transition: % -> %',
                OLD.execution_status,
                NEW.execution_status;
        END IF;
    END IF;

    -- Once recorded, the start timestamp is immutable.
    IF OLD.started_at IS NOT NULL
       AND NEW.started_at IS DISTINCT FROM OLD.started_at
    THEN
        RAISE EXCEPTION
            'Execution start timestamp cannot be changed once recorded.';
    END IF;

    -- Once recorded, the completion timestamp is immutable.
    IF OLD.completed_at IS NOT NULL
       AND NEW.completed_at IS DISTINCT FROM OLD.completed_at
    THEN
        RAISE EXCEPTION
            'Execution completion timestamp cannot be changed once recorded.';
    END IF;

    -- A first start timestamp is permitted only when entering
    -- validation or recording an immediate failure.
    IF OLD.started_at IS NULL
       AND NEW.started_at IS NOT NULL
       AND NEW.execution_status NOT IN ('validating', 'failed')
    THEN
        RAISE EXCEPTION
            'Execution can only start when entering validating or recording a failure.';
    END IF;

    -- All started or terminal executions require a start timestamp.
    IF NEW.execution_status IN (
        'validating',
        'running',
        'completed',
        'completed_with_warnings',
        'failed'
    )
    AND NEW.started_at IS NULL
    THEN
        RAISE EXCEPTION
            'Execution status requires a start timestamp.';
    END IF;

    -- Completion timestamps are only valid for terminal statuses.
    IF NEW.completed_at IS NOT NULL
       AND NEW.execution_status NOT IN (
           'completed',
           'completed_with_warnings',
           'failed'
       )
    THEN
        RAISE EXCEPTION
            'Completion timestamp is only permitted for terminal statuses.';
    END IF;

    -- Terminal statuses require a completion timestamp.
    IF NEW.execution_status IN (
        'completed',
        'completed_with_warnings',
        'failed'
    )
    AND NEW.completed_at IS NULL
    THEN
        RAISE EXCEPTION
            'Terminal execution status requires a completion timestamp.';
    END IF;

    RETURN NEW;

END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: scenario_assumptions; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_assumptions (
    assumption_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid NOT NULL,
    assumption_category character varying(40) NOT NULL,
    assumption_key character varying(100) NOT NULL,
    adjustment_method character varying(30) NOT NULL,
    assumption_value numeric(20,6) NOT NULL,
    unit character varying(30) NOT NULL,
    effective_from date,
    effective_to date,
    assumption_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_adjustment_method CHECK (((adjustment_method)::text = ANY ((ARRAY['percentage'::character varying, 'absolute'::character varying, 'multiplier'::character varying])::text[]))),
    CONSTRAINT chk_assumption_category CHECK (((assumption_category)::text = ANY ((ARRAY['revenue'::character varying, 'expense'::character varying, 'cashflow'::character varying, 'liquidity'::character varying, 'working_capital'::character varying, 'payment_behavior'::character varying, 'other'::character varying])::text[]))),
    CONSTRAINT chk_assumption_effective_dates CHECK (((effective_to IS NULL) OR (effective_from IS NULL) OR (effective_to >= effective_from)))
);


--
-- Name: scenario_definitions; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_definitions (
    scenario_id uuid DEFAULT gen_random_uuid() NOT NULL,
    scenario_reference character varying(50) NOT NULL,
    business_id text NOT NULL,
    scenario_name character varying(150) NOT NULL,
    scenario_type character varying(30) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_scenario_type CHECK (((scenario_type)::text = ANY ((ARRAY['baseline'::character varying, 'optimistic'::character varying, 'adverse'::character varying, 'custom'::character varying])::text[])))
);


--
-- Name: scenario_execution_inputs; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_execution_inputs (
    input_id uuid DEFAULT gen_random_uuid() NOT NULL,
    execution_id uuid NOT NULL,
    business_id text NOT NULL,
    forecast_date date NOT NULL,
    forecast_target character varying(50) NOT NULL,
    source_method character varying(50),
    source_origin_date date,
    forecast_horizon integer,
    baseline_forecast_value numeric(20,6) NOT NULL,
    source_reference text NOT NULL,
    source_file_checksum character varying(128),
    input_snapshot jsonb NOT NULL,
    captured_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_execution_input_horizon CHECK (((forecast_horizon IS NULL) OR (forecast_horizon >= 1))),
    CONSTRAINT chk_execution_input_target CHECK (((forecast_target)::text = ANY ((ARRAY['total_credit_inflows'::character varying, 'total_debit_outflows'::character varying, 'net_bank_movement'::character varying])::text[])))
);


--
-- Name: scenario_executions; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_executions (
    execution_id uuid DEFAULT gen_random_uuid() NOT NULL,
    version_id uuid NOT NULL,
    execution_status character varying(30) DEFAULT 'pending'::character varying NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    random_seed bigint,
    execution_notes text,
    error_message text,
    executed_by character varying(100),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    business_id text NOT NULL,
    CONSTRAINT chk_execution_status CHECK (((execution_status)::text = ANY ((ARRAY['pending'::character varying, 'validating'::character varying, 'running'::character varying, 'completed'::character varying, 'completed_with_warnings'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT chk_execution_timestamps CHECK (((completed_at IS NULL) OR ((started_at IS NOT NULL) AND (completed_at >= started_at))))
);


--
-- Name: scenario_results; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_results (
    result_id uuid DEFAULT gen_random_uuid() NOT NULL,
    execution_id uuid NOT NULL,
    business_id text NOT NULL,
    forecast_date date NOT NULL,
    scenario_inflows numeric(20,6),
    scenario_outflows numeric(20,6),
    scenario_net_movement numeric(20,6),
    independent_net_forecast numeric(20,6),
    reconciliation_difference numeric(20,6),
    opening_cash_balance numeric(20,6),
    projected_closing_cash numeric(20,6),
    cash_projection_status character varying(40) DEFAULT 'opening_balance_unverified'::character varying NOT NULL,
    additional_metrics jsonb DEFAULT '{}'::jsonb NOT NULL,
    calculated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_cash_projection_status CHECK (((cash_projection_status)::text = ANY ((ARRAY['opening_balance_unverified'::character varying, 'projected'::character varying, 'insufficient_data'::character varying, 'not_applicable'::character varying])::text[]))),
    CONSTRAINT chk_projected_closing_cash CHECK (((projected_closing_cash IS NULL) OR ((opening_cash_balance IS NOT NULL) AND ((cash_projection_status)::text = 'projected'::text))))
);


--
-- Name: scenario_validation_results; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_validation_results (
    validation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    execution_id uuid NOT NULL,
    validation_category character varying(50) NOT NULL,
    validation_rule character varying(100) NOT NULL,
    validation_status character varying(20) NOT NULL,
    severity character varying(20) NOT NULL,
    validation_message text NOT NULL,
    validation_details jsonb DEFAULT '{}'::jsonb NOT NULL,
    validated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_validation_severity CHECK (((severity)::text = ANY ((ARRAY['info'::character varying, 'low'::character varying, 'medium'::character varying, 'high'::character varying, 'critical'::character varying])::text[]))),
    CONSTRAINT chk_validation_status CHECK (((validation_status)::text = ANY ((ARRAY['passed'::character varying, 'warning'::character varying, 'failed'::character varying])::text[])))
);


--
-- Name: scenario_versions; Type: TABLE; Schema: scenario; Owner: -
--

CREATE TABLE scenario.scenario_versions (
    version_id uuid DEFAULT gen_random_uuid() NOT NULL,
    scenario_id uuid NOT NULL,
    version_number integer NOT NULL,
    configuration_status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    version_notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by character varying(100),
    business_id text NOT NULL,
    CONSTRAINT chk_configuration_status CHECK (((configuration_status)::text = ANY ((ARRAY['draft'::character varying, 'approved'::character varying, 'archived'::character varying])::text[]))),
    CONSTRAINT chk_scenario_version_number CHECK ((version_number >= 1))
);


--
-- Name: scenario_assumptions scenario_assumptions_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_assumptions
    ADD CONSTRAINT scenario_assumptions_pkey PRIMARY KEY (assumption_id);


--
-- Name: scenario_definitions scenario_definitions_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_definitions
    ADD CONSTRAINT scenario_definitions_pkey PRIMARY KEY (scenario_id);


--
-- Name: scenario_definitions scenario_definitions_scenario_reference_key; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_definitions
    ADD CONSTRAINT scenario_definitions_scenario_reference_key UNIQUE (scenario_reference);


--
-- Name: scenario_execution_inputs scenario_execution_inputs_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_execution_inputs
    ADD CONSTRAINT scenario_execution_inputs_pkey PRIMARY KEY (input_id);


--
-- Name: scenario_executions scenario_executions_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_executions
    ADD CONSTRAINT scenario_executions_pkey PRIMARY KEY (execution_id);


--
-- Name: scenario_results scenario_results_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_results
    ADD CONSTRAINT scenario_results_pkey PRIMARY KEY (result_id);


--
-- Name: scenario_validation_results scenario_validation_results_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_validation_results
    ADD CONSTRAINT scenario_validation_results_pkey PRIMARY KEY (validation_id);


--
-- Name: scenario_versions scenario_versions_pkey; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_versions
    ADD CONSTRAINT scenario_versions_pkey PRIMARY KEY (version_id);


--
-- Name: scenario_execution_inputs uq_execution_input_target; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_execution_inputs
    ADD CONSTRAINT uq_execution_input_target UNIQUE (execution_id, forecast_date, forecast_target);


--
-- Name: scenario_definitions uq_scenario_definition_business; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_definitions
    ADD CONSTRAINT uq_scenario_definition_business UNIQUE (scenario_id, business_id);


--
-- Name: scenario_executions uq_scenario_execution_business; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_executions
    ADD CONSTRAINT uq_scenario_execution_business UNIQUE (execution_id, business_id);


--
-- Name: scenario_results uq_scenario_result_period; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_results
    ADD CONSTRAINT uq_scenario_result_period UNIQUE (execution_id, forecast_date);


--
-- Name: scenario_versions uq_scenario_version_business; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_versions
    ADD CONSTRAINT uq_scenario_version_business UNIQUE (version_id, business_id);


--
-- Name: scenario_versions uq_scenario_version_number; Type: CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_versions
    ADD CONSTRAINT uq_scenario_version_number UNIQUE (scenario_id, version_number);


--
-- Name: scenario_executions trg_enforce_execution_lifecycle; Type: TRIGGER; Schema: scenario; Owner: -
--

CREATE TRIGGER trg_enforce_execution_lifecycle BEFORE UPDATE ON scenario.scenario_executions FOR EACH ROW EXECUTE FUNCTION scenario.enforce_execution_lifecycle();


--
-- Name: scenario_execution_inputs fk_execution_input_business; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_execution_inputs
    ADD CONSTRAINT fk_execution_input_business FOREIGN KEY (business_id) REFERENCES processed.business_profiles(business_id);


--
-- Name: scenario_execution_inputs fk_execution_input_business_consistency; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_execution_inputs
    ADD CONSTRAINT fk_execution_input_business_consistency FOREIGN KEY (execution_id, business_id) REFERENCES scenario.scenario_executions(execution_id, business_id);


--
-- Name: scenario_execution_inputs fk_execution_input_execution; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_execution_inputs
    ADD CONSTRAINT fk_execution_input_execution FOREIGN KEY (execution_id) REFERENCES scenario.scenario_executions(execution_id);


--
-- Name: scenario_assumptions fk_scenario_assumption_version; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_assumptions
    ADD CONSTRAINT fk_scenario_assumption_version FOREIGN KEY (version_id) REFERENCES scenario.scenario_versions(version_id);


--
-- Name: scenario_definitions fk_scenario_business; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_definitions
    ADD CONSTRAINT fk_scenario_business FOREIGN KEY (business_id) REFERENCES processed.business_profiles(business_id);


--
-- Name: scenario_executions fk_scenario_execution_version; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_executions
    ADD CONSTRAINT fk_scenario_execution_version FOREIGN KEY (version_id) REFERENCES scenario.scenario_versions(version_id);


--
-- Name: scenario_executions fk_scenario_execution_version_business; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_executions
    ADD CONSTRAINT fk_scenario_execution_version_business FOREIGN KEY (version_id, business_id) REFERENCES scenario.scenario_versions(version_id, business_id);


--
-- Name: scenario_results fk_scenario_result_business; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_results
    ADD CONSTRAINT fk_scenario_result_business FOREIGN KEY (business_id) REFERENCES processed.business_profiles(business_id);


--
-- Name: scenario_results fk_scenario_result_business_consistency; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_results
    ADD CONSTRAINT fk_scenario_result_business_consistency FOREIGN KEY (execution_id, business_id) REFERENCES scenario.scenario_executions(execution_id, business_id);


--
-- Name: scenario_results fk_scenario_result_execution; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_results
    ADD CONSTRAINT fk_scenario_result_execution FOREIGN KEY (execution_id) REFERENCES scenario.scenario_executions(execution_id);


--
-- Name: scenario_validation_results fk_scenario_validation_execution; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_validation_results
    ADD CONSTRAINT fk_scenario_validation_execution FOREIGN KEY (execution_id) REFERENCES scenario.scenario_executions(execution_id);


--
-- Name: scenario_versions fk_scenario_version_business; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_versions
    ADD CONSTRAINT fk_scenario_version_business FOREIGN KEY (scenario_id, business_id) REFERENCES scenario.scenario_definitions(scenario_id, business_id);


--
-- Name: scenario_versions fk_scenario_version_definition; Type: FK CONSTRAINT; Schema: scenario; Owner: -
--

ALTER TABLE ONLY scenario.scenario_versions
    ADD CONSTRAINT fk_scenario_version_definition FOREIGN KEY (scenario_id) REFERENCES scenario.scenario_definitions(scenario_id);


--
-- PostgreSQL database dump complete
--

\unrestrict B104ndr2xy7coYMxMeEvM3BvuifEXwWyLmVemZAc7nmpQLkDgafbeTgd6JTQm6f

