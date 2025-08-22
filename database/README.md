좋습니다! 지금 상태 기준으로 “처음부터 끝까지” 실행순서를 깔끔하게 정리해 드릴게요. (Windows PowerShell 기준)

# 실행 순서

1. 리셋(완전 초기화, 필요 시만)

```powershell
cd D:\work\dev\github\private\mathematics_curriculum_extraction\database
docker compose down -v
```

2. 환경변수(.env) 확인
   `database/.env` 파일에 아래 값이 있어야 합니다:

```
DB_NAME=mathematics_curriculum
DB_SUPERUSER=postgres
DB_SUPERPASS=postgres
DB_PORT=5432

CURRICULUM_ADMIN_USER=curriculum
CURRICULUM_ADMIN_PASS=curriculum
CURRICULUM_WRITER_USER=curriculum_writer
CURRICULUM_WRITER_PASS=curriculum_writer
CURRICULUM_READER_USER=curriculum_reader
CURRICULUM_READER_PASS=curriculum_reader

PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=pgadmin
PGADMIN_PORT=5050
```

3. 컨테이너 기동 (DB + pgAdmin, 스키마/패치 자동 적용)

```powershell
docker compose up -d
docker compose logs --no-color postgres
```

로그에 `CREATE TABLE/VIEW/INDEX`가 주르륵 나오면 성공입니다.

4. (선택) psql로 스키마 확인

```powershell
docker exec -it curriculum-postgres psql -U postgres -d mathematics_curriculum -c "\dn+"
docker exec -it curriculum-postgres psql -U postgres -d mathematics_curriculum -c "\dt curriculum.*"
```

5. 로컬 파이썬 환경 준비(최초 1회)

```powershell
cd D:\work\dev\github\private\mathematics_curriculum_extraction\database
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

6. 데이터 로드용 연결 정보 설정

```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
$env:DB_NAME="mathematics_curriculum"
$env:DB_USER="curriculum"
$env:DB_PASSWORD="curriculum"
$env:DB_SCHEMA="curriculum"
```

7. 데이터 적재 실행

```powershell
python .\scripts\data_load.py
```

로그에 `모든 데이터 로딩 완료! / 데이터 로딩 성공`이 나오면 OK.

8. 적재 결과 간단 검증(선택)

```powershell
docker exec -it curriculum-postgres psql -U postgres -d mathematics_curriculum -c "SELECT * FROM curriculum.v_curriculum_statistics ORDER BY school_type, domain_name;"
```

9. 재적재(증분/덮어쓰기)

* CSV를 수정/추가한 뒤 **7번만 다시 실행**하면 됩니다. 스크립트는 `ON CONFLICT` 업서트로 안전하게 덮어씁니다.
* 스키마를 다시 초기부터 적용하려면 **1→3→7** 순서로 진행하세요.

# 자주 쓰는 유지보수/문제해결

* `permission denied for schema curriculum` 발생 시(로컬 접속계정 권한/서치패스 문제):

```powershell
docker exec -it curriculum-postgres psql -U postgres -d mathematics_curriculum `
  -c "GRANT USAGE ON SCHEMA curriculum TO curriculum;
      GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA curriculum TO curriculum;
      GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA curriculum TO curriculum;
      ALTER ROLE curriculum IN DATABASE mathematics_curriculum SET search_path = curriculum, public;"
```

* 시퀀스 값 보정은 스크립트가 자동 수행합니다. 수동으로 확인/적용하려면:

```powershell
docker exec -it curriculum-postgres psql -U postgres -d mathematics_curriculum `
  -c "SELECT setval('curriculum.content_elements_element_id_seq', (SELECT COALESCE(MAX(element_id),1) FROM curriculum.content_elements));"
```

# (선택) 한 방에 데이터만 다시 넣고 싶을 때

이미 컨테이너가 떠 있고 스키마가 준비된 상태라면, **6 → 7** 두 단계만 실행하면 됩니다.

필요하시면 이 과정을 `.ps1` 스크립트로 묶은 “원클릭” 실행파일도 만들어 드릴게요.
