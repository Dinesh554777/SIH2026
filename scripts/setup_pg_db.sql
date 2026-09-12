-- One-time PostgreSQL provisioning for SIH2026 Phase I-A (run as superuser).
-- Usage:
--   psql -U postgres -h 127.0.0.1 -f scripts/setup_pg_db.sql
-- Replace :APP_PASSWORD with a strong password before running.
-- Idempotent: safe to re-run.

\set ON_ERROR_STOP on

SELECT 'CREATE ROLE sih2026_app LOGIN PASSWORD ' || quote_literal('CHANGE_ME')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sih2026_app')
\gexec

SELECT 'CREATE DATABASE sih2026_app OWNER sih2026_app'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'sih2026_app')
\gexec

SELECT 'CREATE DATABASE sih2026_app_test OWNER sih2026_app'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'sih2026_app_test')
\gexec

-- Application role needs CREATE/append in both databases.
\c sih2026_app
GRANT ALL ON SCHEMA public TO sih2026_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT ALL ON TABLES TO sih2026_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT ALL ON SEQUENCES TO sih2026_app;

\c sih2026_app_test
GRANT ALL ON SCHEMA public TO sih2026_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT ALL ON TABLES TO sih2026_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT ALL ON SEQUENCES TO sih2026_app;

\echo 'Provisioning complete. Update .env with the password you chose.'