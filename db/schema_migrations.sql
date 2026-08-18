-- Migration tracking table — the single source of truth for "has this file run?".
--
-- Applied by BOTH runners (scripts/migrate.sh and scripts/run_migrations.py)
-- before they do anything else, so it bootstraps itself and is never itself a
-- numbered migration.
--
-- Contract both runners implement identically:
--   * a file in db/migrations/*.sql whose basename is NOT in this table is
--     executed, then recorded
--   * a file whose basename IS in this table is skipped, never re-executed
--   * if a recorded file's checksum no longer matches what was applied, the
--     runner warns and still skips it — editing an already-applied migration is
--     something you want to be told about, not something a runner should
--     silently re-apply
--   * --bootstrap records every unrecorded file WITHOUT executing it, for a
--     database whose schema already exists (see the runners' --help)

CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    checksum    TEXT NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE schema_migrations IS
    'One row per applied file in db/migrations. Written by scripts/migrate.sh and scripts/run_migrations.py.';
COMMENT ON COLUMN schema_migrations.checksum IS
    'sha256 of the file contents at the time it was applied; a later mismatch means the file was edited afterwards.';
