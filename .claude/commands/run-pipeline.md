# AI 파이프라인 실행

지식 그래프 구축을 위한 4단계 AI 파이프라인을 실행합니다.

실행 단계:
1. Phase 1: Gemini 2.5로 전체 구조 분석
2. Phase 2: GPT-5로 대량 관계 추출
3. Phase 3: Claude Sonnet으로 관계 정제
4. Phase 4: Claude Opus로 최종 검증

옵션:
- --resume-from N: N단계부터 재개
- --phase-only N: N단계만 실행
- --dry-run: 실제 API 호출 없이 시뮬레이션

```bash
cd knowledge_graph_project
python main.py $ARGUMENTS
```

비용 예상치를 먼저 계산하고 확인을 받은 후 진행해주세요.