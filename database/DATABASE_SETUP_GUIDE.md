# PostgreSQL 데이터베이스 설정 및 데이터 로딩 가이드

## 📋 사전 준비사항

### 1. PostgreSQL 설치
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql

# Windows
# https://www.postgresql.org/download/windows/ 에서 다운로드
```

### 2. Python 패키지 설치
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate  # Windows

# 필요 패키지 설치
pip install -r requirements.txt
```

## 🚀 데이터베이스 설정

### 1. PostgreSQL 서비스 시작
```bash
# Linux
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew services start postgresql

# Windows
# 서비스에서 PostgreSQL 시작
```

### 2. 데이터베이스 및 사용자 생성
```sql
-- PostgreSQL에 superuser로 연결
sudo -u postgres psql

-- 데이터베이스 생성
CREATE DATABASE mathematics_curriculum 
    WITH ENCODING 'UTF8' 
    LC_COLLATE='ko_KR.UTF-8' 
    LC_CTYPE='ko_KR.UTF-8';

-- 사용자 생성 (선택사항)
CREATE USER curriculum_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mathematics_curriculum TO curriculum_user;

-- 연결 종료
\q
```

### 3. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=mathematics_curriculum
# DB_USER=postgres  # 또는 curriculum_user
# DB_PASSWORD=your_actual_password
# DB_SCHEMA=curriculum
```

### 4. 스키마 생성
```bash
# PostgreSQL에 연결하여 스키마 실행
psql -h localhost -U postgres -d mathematics_curriculum -f postgresql_schema.sql
```

## 📊 데이터 로딩

### 1. 기본 실행
```bash
# 모든 데이터 로딩
python load_data.py

# 설정 파일 지정
python load_data.py --config custom_config.json

# 검증만 수행 (실제 삽입 없음)
python load_data.py --dry-run
```

### 2. 로딩 프로세스
1. **기준 데이터**: school_levels, domains, categories
2. **내용 체계**: core_ideas, content_elements
3. **성취기준**: achievement_standards, standard_explanations
4. **용어 기호**: terms_symbols

### 3. 로딩 결과 확인
```sql
-- 전체 통계 확인
SELECT 
    'school_levels' as table_name, COUNT(*) as count FROM curriculum.school_levels
UNION ALL
SELECT 
    'domains' as table_name, COUNT(*) as count FROM curriculum.domains
UNION ALL
SELECT 
    'achievement_standards' as table_name, COUNT(*) as count FROM curriculum.achievement_standards
UNION ALL
SELECT 
    'terms_symbols' as table_name, COUNT(*) as count FROM curriculum.terms_symbols;

-- 학년별 성취기준 수 확인
SELECT * FROM curriculum.v_curriculum_statistics;
```

## 🔍 데이터 검증

### 1. 참조 무결성 확인
```sql
-- 성취기준의 외래키 검증
SELECT 
    COUNT(*) as total_standards,
    COUNT(CASE WHEN sl.level_id IS NULL THEN 1 END) as invalid_level_refs,
    COUNT(CASE WHEN d.domain_id IS NULL THEN 1 END) as invalid_domain_refs
FROM curriculum.achievement_standards ast
    LEFT JOIN curriculum.school_levels sl ON ast.level_id = sl.level_id
    LEFT JOIN curriculum.domains d ON ast.domain_id = d.domain_id;
```

### 2. 데이터 품질 확인
```sql
-- LaTeX 표현이 있는 용어 확인
SELECT 
    term_type,
    COUNT(*) as total_terms,
    COUNT(CASE WHEN latex_expression IS NOT NULL THEN 1 END) as latex_terms
FROM curriculum.terms_symbols
GROUP BY term_type;

-- 성취기준 코드 형식 확인
SELECT 
    COUNT(*) as total_standards,
    COUNT(CASE WHEN standard_code ~ '^[0-9]{1}수[0-9]{2}-[0-9]{2}$' THEN 1 END) as valid_format
FROM curriculum.achievement_standards;
```

## 📈 성능 최적화

### 1. 인덱스 확인
```sql
-- 인덱스 사용 상황 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'curriculum'
ORDER BY idx_tup_read DESC;
```

### 2. 쿼리 성능 분석
```sql
-- 성취기준 검색 성능 테스트
EXPLAIN ANALYZE
SELECT * FROM curriculum.search_achievement_standards('분수');

-- 전문 검색 성능 테스트
EXPLAIN ANALYZE
SELECT * FROM curriculum.achievement_standards
WHERE to_tsvector('korean', standard_content) @@ plainto_tsquery('korean', '이해');
```

## 🔧 문제 해결

### 1. 일반적인 오류

#### 연결 오류
```
psycopg2.OperationalError: could not connect to server
```
**해결방법**: 
- PostgreSQL 서비스 상태 확인
- 방화벽 설정 확인
- pg_hba.conf 설정 확인

#### 인코딩 오류
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```
**해결방법**:
- CSV 파일 인코딩 확인 (UTF-8로 저장)
- 로딩 스크립트의 encoding 파라미터 조정

#### 외래키 제약 위반
```
psycopg2.IntegrityError: insert or update on table violates foreign key constraint
```
**해결방법**:
- 참조 테이블 데이터 먼저 로딩
- 데이터 일관성 검사

### 2. 로그 파일 확인
```bash
# 로딩 로그 확인
tail -f data_loading.log

# PostgreSQL 로그 확인 (Ubuntu)
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## 🎯 고급 활용

### 1. 백업 및 복원
```bash
# 전체 데이터베이스 백업
pg_dump -h localhost -U postgres mathematics_curriculum > backup.sql

# 스키마만 백업
pg_dump -h localhost -U postgres -n curriculum mathematics_curriculum > schema_backup.sql

# 복원
psql -h localhost -U postgres mathematics_curriculum < backup.sql
```

### 2. 데이터 업데이트
```python
# 기존 데이터 업데이트
python load_data.py --update-mode

# 특정 테이블만 업데이트
python load_data.py --tables achievement_standards,terms_symbols
```

### 3. API 서버 연동
```python
# 데이터베이스 연결 풀 설정
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # 최소/최대 연결 수
    host='localhost',
    database='mathematics_curriculum',
    user='postgres',
    password='password'
)
```

## 📞 지원 및 문의

- **GitHub Issues**: 프로젝트 저장소의 Issues 탭
- **문서**: README.md 및 docs/ 폴더 참조
- **로그 분석**: data_loading.log 파일 확인

---

**업데이트**: 2024-12-19  
**버전**: 1.0.0
