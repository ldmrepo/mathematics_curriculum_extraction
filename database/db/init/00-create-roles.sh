#!/usr/bin/env bash
set -euo pipefail

# 환경변수 (postgres 컨테이너에서 주입됨)
DB_NAME="${DB_NAME:-mathematics_curriculum}"
DB_SUPERUSER="${POSTGRES_USER:-${DB_SUPERUSER:-postgres}}"
DB_SUPERPASS="${POSTGRES_PASSWORD:-${DB_SUPERPASS:-postgres}}"

CURR_ADMIN_USER="${CURRICULUM_ADMIN_USER:-curriculum_admin}"
CURR_ADMIN_PASS="${CURRICULUM_ADMIN_PASS:-curriculum_admin_password}"
CURR_WRITER_USER="${CURRICULUM_WRITER_USER:-curriculum_writer}"
CURR_WRITER_PASS="${CURRICULUM_WRITER_PASS:-curriculum_writer_password}"
CURR_READER_USER="${CURRICULUM_READER_USER:-curriculum_reader}"
CURR_READER_PASS="${CURRICULUM_READER_PASS:-curriculum_reader_password}"

echo "[init] create database and roles ..."

# DB는 POSTGRES_DB로 이미 생성되지만 안전하게 재확인
psql -v ON_ERROR_STOP=1 --username "$DB_SUPERUSER" <<-EOSQL
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
      PERFORM dblink_exec('dbname=' || current_database(), 'CREATE DATABASE $DB_NAME');
    END IF;
  END
  \$\$;
EOSQL

# 앱용 롤 생성/비번 설정/권한
psql -v ON_ERROR_STOP=1 --username "$DB_SUPERUSER" --dbname "$DB_NAME" <<-EOSQL
  -- 존재 시 비번만 재설정
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$CURR_ADMIN_USER') THEN
      CREATE ROLE $CURR_ADMIN_USER LOGIN PASSWORD '$CURR_ADMIN_PASS';
    ELSE
      EXECUTE format('ALTER ROLE %I LOGIN PASSWORD %L', '$CURR_ADMIN_USER', '$CURR_ADMIN_PASS');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$CURR_WRITER_USER') THEN
      CREATE ROLE $CURR_WRITER_USER LOGIN PASSWORD '$CURR_WRITER_PASS';
    ELSE
      EXECUTE format('ALTER ROLE %I LOGIN PASSWORD %L', '$CURR_WRITER_USER', '$CURR_WRITER_PASS');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='$CURR_READER_USER') THEN
      CREATE ROLE $CURR_READER_USER LOGIN PASSWORD '$CURR_READER_PASS';
    ELSE
      EXECUTE format('ALTER ROLE %I LOGIN PASSWORD %L', '$CURR_READER_USER', '$CURR_READER_PASS');
    END IF;
  END
  \$\$;

  -- 스키마/오브젝트 권한은 스키마 생성 이후(01, 02 파일에서) 다시 부여됨.
EOSQL

echo "[init] roles ready."
