#!/usr/bin/env bash
set -euo pipefail

# 환경변수 (postgres 컨테이너에서 주입됨)
DB_NAME="${POSTGRES_DB:-mathematics_curriculum}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres123}"

echo "[init] Database initialization..."

# 데이터베이스는 POSTGRES_DB 환경변수로 자동 생성되므로 추가 작업 불필요
# 스키마 생성 및 테이블 설정은 01-schema-v1.2.0.sql과 02-patch-v1.3.0.sql에서 처리

echo "[init] Database ready."