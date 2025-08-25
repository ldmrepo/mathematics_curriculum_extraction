# 데이터베이스 초기화 명령

Docker 환경을 시작하고 데이터베이스를 초기화합니다.

다음 작업을 수행해주세요:
1. Docker Compose로 PostgreSQL과 Neo4j 시작
2. 스키마 생성 확인
3. CSV 데이터 임포트
4. 데이터 검증 (총 181개 성취기준, 843개 성취수준)
5. 연결 테스트

명령:
```bash
cd database
docker-compose up -d
python scripts/data_load.py
```

추가 요청사항: $ARGUMENTS