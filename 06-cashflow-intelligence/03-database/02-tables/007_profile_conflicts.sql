-- processed.profile_conflicts: Conflicting business profile versions awaiting review
-- Source: 01-data/03-processed/profile-conflicts.csv   (columns are in CSV order, so \copy loads directly)

CREATE TABLE processed.profile_conflicts (
    business_id                   TEXT          NOT NULL,
    canonical_source_record_id    TEXT          NOT NULL,
    conflicting_source_record_id  TEXT          NOT NULL,
    differing_fields              TEXT          NOT NULL,
    status                        TEXT          NOT NULL,
    note                          TEXT          NOT NULL,
    CONSTRAINT pk_profile_conflicts
        PRIMARY KEY (business_id, conflicting_source_record_id),
    CONSTRAINT fk_profile_conflicts_business
        FOREIGN KEY (business_id) REFERENCES processed.business_profiles (business_id),
    CONSTRAINT fk_profile_conflicts_canonical
        FOREIGN KEY (canonical_source_record_id) REFERENCES processed.business_profiles (source_record_id),
    CONSTRAINT ck_profile_conflicts_status
        CHECK (status IN ('needs_review'))
);

COMMENT ON TABLE processed.profile_conflicts IS 'Where a business had more than one profile version, which versions conflict and in which fields. A person must confirm the correct one.';
COMMENT ON COLUMN processed.profile_conflicts.business_id IS 'SME with conflicting profile versions.';
COMMENT ON COLUMN processed.profile_conflicts.canonical_source_record_id IS 'Version currently used as the working profile.';
COMMENT ON COLUMN processed.profile_conflicts.conflicting_source_record_id IS 'Conflicting version. Not stored in business_profiles; preserved in the raw and staging layers.';
COMMENT ON COLUMN processed.profile_conflicts.differing_fields IS 'Fields that differ between the two versions, semicolon separated.';
COMMENT ON COLUMN processed.profile_conflicts.status IS 'Review status.';
COMMENT ON COLUMN processed.profile_conflicts.note IS 'Explanation of how the conflict was handled.';
