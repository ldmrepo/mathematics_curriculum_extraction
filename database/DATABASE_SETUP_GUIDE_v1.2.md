# 데이터베이스 설정 가이드 v1.2

## 변경 사항 (v1.2)

### 새로운 기능
1. **성취기준별 성취수준 테이블 추가**
   - `achievement_levels`: 성취수준 레벨 정의 (A~E)
   - `standard_achievement_levels`: 각 성취기준별 성취수준 설명
   - `domain_achievement_levels`: 영역별 성취수준 설명

2. **새로운 뷰 추가**
   - `v_standard_achievement_levels_detail`: 성취기준별 성취수준 상세 뷰
   - `v_domain_achievement_levels_detail`: 영역별 성취수준 상세 뷰

3. **새로운 함수 추가**
   - `search_achievement_levels()`: 성취수준 검색
   - `get_standard_levels()`: 특정 성취기준의 모든 성취수준 조회

## 시스템 요구사항

- PostgreSQL 14.0 이상
- Python 3.8 이상
- psycopg2 2.9 이상

## 설치 방법

### 1. PostgreSQL 설치

#### Windows
```bash
# PostgreSQL 다운로드 및 설치
https://www.postgresql.org/download/windows/
```

#### macOS
```bash
brew install postgresql@14
brew services start postgresql@14
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql-14 postgresql-client-14
sudo systemctl start postgresql
```

### 2. 데이터베이스 생성

```sql
-- PostgreSQL에 접속
psql -U postgres

-- 데이터베이스 생성
CREATE DATABASE mathematics_curriculum 
    WITH ENCODING 'UTF8' 
    LC_COLLATE='ko_KR.UTF-8' 
    LC_CTYPE='ko_KR.UTF-8';

-- 사용자 생성
CREATE USER curriculum_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mathematics_curriculum TO curriculum_admin;

-- 데이터베이스 연결
\c mathematics_curriculum

-- 스키마 생성 스크립트 실행
\i postgresql_schema_v1.2.sql
```

### 3. Python 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일 생성:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mathematics_curriculum
DB_USER=curriculum_admin
DB_PASSWORD=your_password
```

### 5. 데이터 로딩

```bash
# 데이터 로딩 스크립트 실행
python load_data_v1.2.py
```

## 데이터 구조

### 성취수준 데이터 구조

#### achievement_levels (성취수준 레벨)
- `level_code`: A, B, C, D, E
- `level_name`: 매우 우수, 우수, 보통, 기초, 기초 미달
- `level_order`: 1~5 (정렬용)
- `description`: 레벨 설명

#### standard_achievement_levels (성취기준별 성취수준)
- `standard_id`: 성취기준 ID (외래키)
- `level_code`: 성취수준 레벨 (A~E)
- `level_description`: 해당 수준의 상세 설명

#### domain_achievement_levels (영역별 성취수준)
- `level_id`: 학교급 ID (외래키)
- `domain_id`: 영역 ID (외래키)
- `level_code`: 성취수준 레벨 (A~E)
- `category_id`: 범주 ID (외래키)
- `level_description`: 해당 수준의 상세 설명

## 주요 쿼리 예제

### 1. 특정 성취기준의 모든 성취수준 조회

```sql
-- 함수 사용
SELECT * FROM get_standard_levels('9수01-01');

-- 직접 쿼리
SELECT 
    al.level_code,
    al.level_name,
    sal.level_description
FROM standard_achievement_levels sal
    JOIN achievement_standards ast ON sal.standard_id = ast.standard_id
    JOIN achievement_levels al ON sal.level_code = al.level_code
WHERE ast.standard_code = '9수01-01'
ORDER BY al.level_order;
```

### 2. 영역별 성취수준 조회

```sql
SELECT 
    sl.grade_range,
    d.domain_name,
    c.category_name,
    al.level_code,
    al.level_name,
    dal.level_description
FROM domain_achievement_levels dal
    JOIN school_levels sl ON dal.level_id = sl.level_id
    JOIN domains d ON dal.domain_id = d.domain_id
    JOIN categories c ON dal.category_id = c.category_id
    JOIN achievement_levels al ON dal.level_code = al.level_code
WHERE sl.grade_range = '중학교 1~3학년'
    AND d.domain_name = '수와 연산'
ORDER BY c.category_order, al.level_order;
```

### 3. 성취수준 검색

```sql
-- 특정 키워드로 성취수준 검색
SELECT * FROM search_achievement_levels('소인수분해');
```

### 4. 성취기준과 성취수준 통계

```sql
SELECT 
    sl.grade_range,
    d.domain_name,
    COUNT(DISTINCT ast.standard_id) as standard_count,
    COUNT(DISTINCT sal.sal_id) as level_count,
    COUNT(DISTINCT sal.sal_id)::float / COUNT(DISTINCT ast.standard_id) / 5 * 100 as completion_rate
FROM school_levels sl
    CROSS JOIN domains d
    LEFT JOIN achievement_standards ast 
        ON sl.level_id = ast.level_id AND d.domain_id = ast.domain_id
    LEFT JOIN standard_achievement_levels sal 
        ON ast.standard_id = sal.standard_id
GROUP BY sl.level_id, sl.grade_range, d.domain_id, d.domain_name
ORDER BY sl.level_id, d.domain_order;
```

## 데이터 검증

### 1. 전체 데이터 통계

```sql
SELECT 
    '학교급' as category, COUNT(*) as count FROM school_levels
UNION ALL
SELECT '영역', COUNT(*) FROM domains
UNION ALL
SELECT '범주', COUNT(*) FROM categories
UNION ALL
SELECT '성취수준 레벨', COUNT(*) FROM achievement_levels
UNION ALL
SELECT '성취기준', COUNT(*) FROM achievement_standards
UNION ALL
SELECT '성취기준별 성취수준', COUNT(*) FROM standard_achievement_levels
UNION ALL
SELECT '영역별 성취수준', COUNT(*) FROM domain_achievement_levels
UNION ALL
SELECT '내용 요소', COUNT(*) FROM content_elements
UNION ALL
SELECT '용어/기호', COUNT(*) FROM terms_symbols;
```

### 2. 성취수준 완성도 확인

```sql
-- 성취기준별 성취수준 완성도 (각 성취기준당 5개 레벨이 있어야 함)
SELECT 
    ast.standard_code,
    COUNT(sal.level_code) as level_count,
    CASE 
        WHEN COUNT(sal.level_code) = 5 THEN '완료'
        ELSE '미완료'
    END as status
FROM achievement_standards ast
    LEFT JOIN standard_achievement_levels sal ON ast.standard_id = sal.standard_id
GROUP BY ast.standard_id, ast.standard_code
HAVING COUNT(sal.level_code) < 5
ORDER BY ast.standard_code;
```

## 백업 및 복원

### 백업

```bash
# 전체 데이터베이스 백업
pg_dump -U curriculum_admin -d mathematics_curriculum -F c -b -v -f backup_v1.2_$(date +%Y%m%d).backup

# 스키마만 백업
pg_dump -U curriculum_admin -d mathematics_curriculum -s > schema_backup_v1.2.sql

# 데이터만 백업
pg_dump -U curriculum_admin -d mathematics_curriculum -a --inserts > data_backup_v1.2.sql
```

### 복원

```bash
# 전체 복원
pg_restore -U curriculum_admin -d mathematics_curriculum -v backup_v1.2_20250121.backup

# SQL 파일 복원
psql -U curriculum_admin -d mathematics_curriculum < schema_backup_v1.2.sql
psql -U curriculum_admin -d mathematics_curriculum < data_backup_v1.2.sql
```

## 트러블슈팅

### 1. 인코딩 문제

```sql
-- 데이터베이스 인코딩 확인
SELECT datname, pg_encoding_to_char(encoding) 
FROM pg_database 
WHERE datname = 'mathematics_curriculum';

-- 클라이언트 인코딩 설정
SET client_encoding = 'UTF8';
```

### 2. 권한 문제

```sql
-- 권한 확인
\du

-- 권한 부여
GRANT ALL PRIVILEGES ON SCHEMA curriculum TO curriculum_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA curriculum TO curriculum_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA curriculum TO curriculum_admin;
```

### 3. 성능 최적화

```sql
-- 통계 업데이트
ANALYZE;

-- 인덱스 재구성
REINDEX SCHEMA curriculum;

-- 쿼리 실행 계획 확인
EXPLAIN ANALYZE [쿼리];
```

## 버전 히스토리

- **v1.0.0** (2024-12-19): 초기 버전
- **v1.1.0** (2025-01-21): 학습 요소 테이블 추가, 용어와 기호 해설 지원
- **v1.2.0** (2025-01-21): 성취기준별/영역별 성취수준 테이블 및 관련 기능 추가

## 문의사항

데이터베이스 관련 문의사항이 있으시면 이슈를 등록해 주세요.
