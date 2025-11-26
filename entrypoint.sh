#!/bin/bash

# 에러 발생 시 스크립트 중단
set -e

echo "🔄 Waiting for database to be ready..."

# 데이터베이스가 준비될 때까지 대기 (최대 30초)
MAX_RETRIES=30
RETRY_COUNT=0

until PGPASSWORD="${POSTGRES_PASSWORD:-tinolife123}" psql -h "db" -U "${POSTGRES_USER:-tinolife}" -d "${POSTGRES_DB:-tinolife}" -c '\q' 2>/dev/null; do
  RETRY_COUNT=$((RETRY_COUNT+1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "❌ Database connection timeout after ${MAX_RETRIES} attempts"
    exit 1
  fi
  echo "⏳ Waiting for PostgreSQL... (${RETRY_COUNT}/${MAX_RETRIES})"
  sleep 1
done

echo "✅ Database is ready!"
echo ""
echo "🔄 Checking database migration status..."

# 현재 마이그레이션 버전 확인
echo "📊 Current migration version:"
pipenv run alembic current 2>&1 | grep -E "^[a-f0-9]+|^INFO" || echo "   ⚠️  No migrations applied yet"

echo ""
echo "📊 Target migration version:"
pipenv run alembic heads 2>&1 | grep -E "^[a-f0-9]+" || echo "   ⚠️  No migration files found"

echo ""
echo "🔄 Applying database migrations..."

# Alembic 마이그레이션 실행
if pipenv run alembic upgrade head 2>&1; then
  echo "✅ Migrations applied successfully!"
else
  echo "❌ Migration failed!"
  exit 1
fi
echo ""
echo "🌱 Seeding initial data..."

# 초기 데이터 시딩 실행
python scripts/seed_initial_data.py

echo "✅ Seeding completed!"
echo ""
echo "🚀 Starting application..."

# 전달된 명령 실행
exec "$@"
