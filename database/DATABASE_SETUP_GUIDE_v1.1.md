# 수학과 교육과정 데이터베이스 설정 가이드

## 📋 목차
1. [개요](#개요)
2. [필요 사항](#필요-사항)
3. [PostgreSQL 설치](#postgresql-설치)
4. [데이터베이스 설정](#데이터베이스-설정)
5. [스키마 생성](#스키마-생성)
6. [데이터 로딩](#데이터-로딩)
7. [검증](#검증)
8. [문제 해결](#문제-해결)

## 개요

이 가이드는 2022 개정 수학과 교육과정 데이터를 PostgreSQL 데이터베이스에 설정하는 방법을 설명합니다.

### 버전 정보
- **스키마 버전**: 1.1.0 (2025-01-21 업데이트)
- **데이터 로더 버전**: 1.1.0
- **PostgreSQL 권장 버전**: 14.0 이상
- **Python 권장 버전**: 3.8 이상

## 필요 사항

### 소프트웨어
- PostgreSQL 14.0 이상
- Python 3.8 이상
- pip (Python 패키지 관리자)

### Python 패키지
```bash
pip install -r requirements.txt
```

또는 개별 설치:
```bash
pip install psycopg2-binary pandas python-dotenv
```

## PostgreSQL 설치

### Windows
1. [PostgreSQL 공식 사이트](https://www.postgresql.org/download/windows/)에서 다운로드
2. 설치 마법사 실행
3. 설치 중 다음 정보 기록:
   - 포트 번호 (기본: 5432)
   - 관리자 비밀번호

### macOS
```bash
# Homebrew 사용
brew install postgresql
brew services start postgresql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## 데이터베이스 설정

### 1. PostgreSQL 접속
```bash
psql -U postgres
```

### 2. 데이터베이스 생성
```sql
-- 데이터베이스 생성
CREATE DATABASE mathematics_curriculum 
    WITH ENCODING 'UTF8' 
    LC_COLLATE='ko_KR.UTF-8' 
    LC_CTYPE='ko_KR.UTF-8';

-- 데이터베이스 연결
\c mathematics_curriculum

-- 사용자 생성 (선택사항)
CREATE USER curriculum_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE mathematics_curriculum TO curriculum_user;
```

### 3. 한글 설정 (Windows의 경우)
Windows에서 한글 정렬이 지원되지 않는 경우:
```sql
CREATE DATABASE mathematics_curriculum 
    WITH ENCODING 'UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C';
```

## 스키마 생성

### 1. 스키마 파일 실행
```bash
# PostgreSQL 명령줄에서
psql -U postgres -d mathematics_curriculum -f postgresql_schema_v1.1.sql

# 또는 psql 내에서
\c mathematics_curriculum
\i postgresql_schema_v1.1.sql
```

### 2. 스키마 확인
```sql
-- 스키마 목록 확인
\dn

-- 테이블 목록 확인
\dt curriculum.*

-- 뷰 목록 확인
\dv curriculum.*
```

## 데이터 로딩

### 1. 환경 변수 설정
`.env` 파일 생성:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mathematics_curriculum
DB_USER=postgres
DB_PASSWORD=your_password
DB_SCHEMA=curriculum
```

### 2. 데이터 로딩 실행
```bash
# 기본 실행
python load_data_v1.1.py

# 검증만 실행 (데이터 삽입 안 함)
python load_data_v1.1.py --dry-run

# 설정 파일 지정
python load_data_v1.1.py --config config.json
```

### 3. 로딩 진행 상황
로딩 중 다음과 같은 메시지가 표시됩니다:
```
2025-01-21 10:00:00 - INFO - 🚀 수학과 교육과정 데이터 로딩 시작
2025-01-21 10:00:01 - INFO - === 기준 데이터 로딩 시작 ===
2025-01-21 10:00:02 - INFO - school_levels 테이블에 4개 레코드 삽입 완료
...
2025-01-21 10:00:30 - INFO - ✅ 모든 데이터 로딩 완료 및 커밋
```

## 검증

### 1. 데이터 카운트 확인
```sql
-- 전체 통계
SELECT 
    '학교급' as category, COUNT(*) as count FROM curriculum.school_levels
UNION ALL
SELECT '영역', COUNT(*) FROM curriculum.domains
UNION ALL
SELECT '성취기준', COUNT(*) FROM curriculum.achievement_standards
UNION ALL
SELECT '성취기준 해설', COUNT(*) FROM curriculum.standard_explanations
UNION ALL
SELECT '용어/기호', COUNT(*) FROM curriculum.terms_symbols;
```

예상 결과:
```
category        | count
----------------+-------
학교급          |     4
영역            |     4
성취기준        |   181
성취기준 해설   |   200+
용어/기호       |   600+
```

### 2. 학년별 성취기준 확인
```sql
SELECT 
    sl.grade_range,
    d.domain_name,
    COUNT(ast.standard_id) as standard_count
FROM curriculum.school_levels sl
    CROSS JOIN curriculum.domains d
    LEFT JOIN curriculum.achievement_standards ast 
        ON sl.level_id = ast.level_id AND d.domain_id = ast.domain_id
GROUP BY sl.level_id, sl.grade_range, d.domain_id, d.domain_name
ORDER BY sl.level_id, d.domain_order;
```

### 3. 성취기준 검색 테스트
```sql
-- 함수 사용 예시
SELECT * FROM curriculum.search_achievement_standards('분수');

-- 용어 검색 예시
SELECT * FROM curriculum.search_terms_symbols('삼각형');
```

### 4. 뷰 확인
```sql
-- 성취기준 상세 정보
SELECT * FROM curriculum.v_achievement_standards_detail LIMIT 5;

-- 교육과정 통계
SELECT * FROM curriculum.v_curriculum_statistics;

-- 용어와 기호 상세
SELECT * FROM curriculum.v_terms_symbols_detail 
WHERE term_type = '기호' LIMIT 10;
```

## 문제 해결

### 1. 인코딩 오류
```
ERROR: invalid byte sequence for encoding "UTF8"
```
**해결**: CSV 파일을 UTF-8로 저장하거나 로더에서 encoding 파라미터 조정

### 2. 권한 오류
```
ERROR: permission denied for schema curriculum
```
**해결**:
```sql
GRANT ALL ON SCHEMA curriculum TO your_user;
GRANT ALL ON ALL TABLES IN SCHEMA curriculum TO your_user;
```

### 3. 외래키 제약 위반
```
ERROR: insert or update on table violates foreign key constraint
```
**해결**: 데이터 로딩 순서 확인 (기준 데이터 → 내용 체계 → 성취기준 → 용어)

### 4. 중복 키 오류
```
ERROR: duplicate key value violates unique constraint
```
**해결**: 
- 기존 데이터 삭제 후 재로딩
- 또는 UPSERT 사용 (ON CONFLICT DO UPDATE)

### 5. 메모리 부족
대용량 데이터 로딩 시:
```python
# load_data_v1.1.py의 page_size 조정
execute_values(cursor, sql, values, template=None, page_size=100)  # 기본값: 1000
```

## 백업 및 복원

### 백업
```bash
# 전체 데이터베이스 백업
pg_dump -U postgres mathematics_curriculum > backup.sql

# 스키마만 백업
pg_dump -U postgres -s mathematics_curriculum > schema_backup.sql

# 데이터만 백업
pg_dump -U postgres -a mathematics_curriculum > data_backup.sql

# 압축 백업
pg_dump -U postgres -F c mathematics_curriculum > backup.dump
```

### 복원
```bash
# SQL 파일 복원
psql -U postgres mathematics_curriculum < backup.sql

# 압축 파일 복원
pg_restore -U postgres -d mathematics_curriculum backup.dump
```

## 유지보수

### 1. 통계 업데이트
```sql
ANALYZE curriculum.achievement_standards;
ANALYZE curriculum.terms_symbols;
```

### 2. 인덱스 재구성
```sql
REINDEX SCHEMA curriculum;
```

### 3. 공간 정리
```sql
VACUUM FULL curriculum.achievement_standards;
```

## 추가 리소스

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [psycopg2 문서](https://www.psycopg.org/docs/)
- [2022 개정 수학과 교육과정](https://www.moe.go.kr/)

## 지원

문제가 발생하거나 질문이 있는 경우:
1. `loading_report.json` 파일 확인
2. `data_loading.log` 파일 확인
3. GitHub Issues에 문의

---
작성일: 2024-12-19
수정일: 2025-01-21
버전: 1.1.0
