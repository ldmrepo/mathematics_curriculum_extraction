# 📊 수학 교육과정 지식 그래프 대시보드 시각화 아이디어

## 프로젝트 개요
2022 개정 수학과 교육과정의 지식 그래프를 기반으로 한 종합 대시보드 구축

### 데이터 현황
- **PostgreSQL**: 성취기준 181개, 성취수준 663개, 내용요소 291개, 용어/기호 362개
- **Neo4j**: 노드 852개, 관계 1,193개, AI 추출 관계 152개
- **데이터 품질**: 참조 무결성 100%, 순환 참조 0개, 고립 노드 0개

---

## 1️⃣ 메인 대시보드 (Overview Dashboard)

### 1.1 핵심 지표 카드 (Key Metrics Cards)
```python
# Streamlit metric cards
st.metric("총 성취기준", "181개", "초등 121, 중등 60")
st.metric("총 성취수준", "663개", "평균 3.66개/성취기준")
st.metric("관계 연결", "1,193개", "AI 추출 152개")
st.metric("그래프 연결성", "91.2%", "고립 노드 0개")
```

### 1.2 학년별 분포 시각화
- **도넛 차트**: 초등(66.85%) vs 중등(33.15%) 비율
- **Stacked Bar Chart**: 학년군별 영역 분포
  - 초등 1-2: 29개
  - 초등 3-4: 47개
  - 초등 5-6: 45개
  - 중학교: 60개

### 1.3 영역별 분포 매트릭스
```python
# Heatmap: 학년 × 영역
data = {
    '도형과 측정': [10, 18, 24, 24],  # 76개 (42%)
    '수와 연산': [12, 16, 12, 12],     # 52개 (28.7%)
    '변화와 관계': [4, 8, 5, 15],      # 32개 (17.7%)
    '자료와 가능성': [3, 5, 4, 9]      # 21개 (11.6%)
}
```

---

## 2️⃣ 지식 그래프 탐색기 (Knowledge Graph Explorer)

### 2.1 인터랙티브 네트워크 그래프
```python
# Pyvis Network Visualization
from pyvis.network import Network
import networkx as nx

net = Network(height='750px', width='100%', bgcolor='#222222')
net.barnes_hut(gravity=-80000, central_gravity=0.3)

# Node styling by type
node_colors = {
    'AchievementStandard': '#4CAF50',
    'AchievementLevel': '#2196F3',
    'GradeLevel': '#FF9800',
    'Domain': '#9C27B0'
}

# Edge styling by relationship type
edge_colors = {
    'PREREQUISITE': '#FF5722',      # 108개
    'RELATED_TO': '#03A9F4',        # 36개
    'HAS_LEVEL': '#8BC34A',         # 663개
    'CONTAINS_STANDARD': '#FFC107'   # 362개
}
```

### 2.2 필터링 패널
- **학년 필터**: 체크박스로 다중 선택
- **영역 필터**: 드롭다운 멀티셀렉트
- **관계 유형 필터**: 토글 버튼
- **검색**: 성취기준 코드/키워드 자동완성

### 2.3 노드 상세 정보 패널
- 호버 시: 간단 정보 툴팁
- 클릭 시: 사이드바에 상세 정보
  - 성취기준 내용
  - 연결된 성취수준
  - 선수/후속 학습
  - AI 추출 관계 및 신뢰도

---

## 3️⃣ 학습 경로 분석 (Learning Path Analysis)

### 3.1 선수학습 경로 시각화
```python
# Sankey Diagram: 지식 흐름
import plotly.graph_objects as go

fig = go.Figure(data=[go.Sankey(
    node = dict(
        pad = 15,
        thickness = 20,
        label = grade_levels + domains + standards,
        color = colors
    ),
    link = dict(
        source = source_indices,
        target = target_indices,
        value = weights
    )
)])
```

### 3.2 최장 경로 분석 (Critical Path)
- **최대 4단계 체인** 시각화
- 시작점 → 종료점 경로 하이라이트
- 병목 구간 식별

### 3.3 계층적 구조 탐색
```python
# Sunburst Chart: 계층 구조
fig = px.sunburst(
    data_frame=df,
    path=['학년군', '영역', '성취기준코드'],
    values='성취수준_수',
    color='평균_난이도'
)
```

---

## 4️⃣ 성취수준 분석 대시보드

### 4.1 수준별 분포 히트맵
```python
# 초등: A(상), B(중), C(하)
# 중등: A(상), B(중상), C(중), D(중하), E(하)

heatmap_data = {
    '초등 1-2': {'A': 85, 'B': 87, 'C': 42},
    '초등 3-4': {'A': 120, 'B': 124, 'C': 65},
    '초등 5-6': {'A': 95, 'B': 98, 'C': 51},
    '중학교': {'A': 60, 'B': 62, 'C': 64, 'D': 58, 'E': 55}
}
```

### 4.2 난이도 진행 곡선
- X축: 학년 진행
- Y축: 평균 난이도
- 영역별 색상 구분

### 4.3 성취수준 상세 뷰어
- 선택한 성취기준의 수준별 설명
- 평가 기준 표시
- 관련 문항 예시 연결

---

## 5️⃣ AI 분석 인사이트 대시보드

### 5.1 모델별 성능 비교
```python
# Radar Chart: 모델 성능
categories = ['정확도', '처리속도', '비용효율', '관계품질', '추론능력']

gpt4o_scores = [85, 90, 70, 88, 92]
claude_scores = [88, 85, 75, 90, 95]
gemini_scores = [82, 95, 85, 85, 88]
```

### 5.2 Phase별 처리 현황
| Phase | 모델 | 처리시간 | 비용 | 결과 |
|-------|------|---------|------|------|
| Phase 1 | Gemini 2.5 | 58초 | $0.007 | 기초설계 완료 |
| Phase 2 | GPT-4o | 142초 | $0.123 | 152개 관계 추출 |
| Phase 3 | Claude Sonnet | 720초 | $0.147 | 170개 관계 정제 |
| Phase 4 | GPT-4o | 28초 | $0.026 | 검증 완료 |

### 5.3 AI 추출 관계 품질
- **Weight 분포**: 0.58-0.95 (평균 0.78)
- **관계 유형별 신뢰도**
  - prerequisite: 0.85
  - related_to: 0.72
  - similar_to: 0.68

---

## 6️⃣ 갭 분석 및 개선 제안

### 6.1 연결 누락 영역 매트릭스
```python
# Gap Analysis Bubble Chart
fig = px.scatter(
    df,
    x='expected_connections',
    y='actual_connections',
    size='gap_size',
    color='domain',
    hover_data=['standard_code', 'gap_percentage']
)
```

### 6.2 개선 우선순위 테이블
| 순위 | 영역 | 문제 | 개선안 | 우선도 |
|------|------|------|--------|--------|
| 1 | 관계 테이블 | 비어있음 (8개) | AI 파이프라인 실행 | 🔴 높음 |
| 2 | 용어-성취기준 | 연결 없음 | 자동 매핑 개발 | 🟡 중간 |
| 3 | 역량-성취기준 | 미연결 | 수동 매핑 | 🟢 낮음 |

---

## 7️⃣ 실시간 쿼리 인터페이스

### 7.1 자연어 질의 시스템
```python
# 예시 질의
user_query = "초등 3학년 분수 관련 성취기준 보여줘"

# 자동 변환
cypher_query = """
MATCH (g:GradeLevel {name: '초등 3-4학년군'})-[:CONTAINS_STANDARD]->(s:AchievementStandard)
WHERE s.description CONTAINS '분수'
RETURN s
"""
```

### 7.2 Cypher 쿼리 빌더
- 드래그 앤 드롭 인터페이스
- 자동 완성 지원
- 쿼리 히스토리 저장

### 7.3 결과 시각화 옵션
- 테이블 뷰
- 그래프 뷰
- 차트 뷰
- JSON 익스포트

---

## 8️⃣ 비교 분석 대시보드

### 8.1 Before/After 비교
```python
# Parallel Coordinates Plot
fig = px.parallel_coordinates(
    df,
    dimensions=['phase2_relations', 'phase3_refined', 'phase4_validated'],
    color='improvement_score'
)
```

### 8.2 시간별 변화 추적
- 타임라인 슬라이더
- 애니메이션 재생
- 변화 하이라이트

---

## 9️⃣ 보고서 생성 모듈

### 9.1 자동 보고서 템플릿
- **성취기준 분석 보고서**
  - 기본 정보
  - 연결 관계
  - 성취수준
  - 학습 경로
  
- **학년별 교육과정 보고서**
  - 영역별 분포
  - 핵심 성취기준
  - 난이도 진행
  
- **AI 분석 결과 보고서**
  - 추출된 관계
  - 신뢰도 평가
  - 개선 제안

### 9.2 내보내기 옵션
- PDF (보고서용)
- PPT (발표용)
- Excel (데이터)
- JSON (개발용)

---

## 🛠️ 기술 스택 및 구현

### Frontend
```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import networkx as nx
import pandas as pd
```

### Backend
```python
from neo4j import GraphDatabase
import psycopg2
from fastapi import FastAPI
import asyncio
```

### 레이아웃 구조
```python
# app.py
st.set_page_config(
    page_title="수학 교육과정 지식 그래프",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바
with st.sidebar:
    page = st.selectbox("대시보드 선택", [
        "📊 메인 대시보드",
        "🕸️ 그래프 탐색기",
        "🛤️ 학습 경로",
        "📈 성취수준 분석",
        "🤖 AI 인사이트",
        "⚠️ 갭 분석",
        "💬 쿼리 인터페이스",
        "📊 비교 분석",
        "📄 보고서 생성"
    ])

# 메인 컨텐츠
if page == "📊 메인 대시보드":
    display_main_dashboard()
elif page == "🕸️ 그래프 탐색기":
    display_graph_explorer()
# ... 등
```

---

## 🚀 구현 우선순위

### Phase 1 (필수)
1. ✅ 메인 대시보드
2. ✅ 인터랙티브 그래프 탐색기
3. ✅ 기본 필터링 기능

### Phase 2 (중요)
4. 🔄 학습 경로 분석
5. 🔄 성취수준 분포 시각화
6. 🔄 실시간 쿼리 인터페이스

### Phase 3 (선택)
7. ⏳ AI 인사이트 대시보드
8. ⏳ 갭 분석 및 개선 제안
9. ⏳ 자동 보고서 생성

---

## 📌 핵심 차별화 요소

1. **AI 기반 관계 추출**: GPT-4o, Claude, Gemini를 활용한 지능형 분석
2. **완전한 교육과정 커버리지**: 181개 성취기준, 663개 성취수준 100% 포함
3. **실시간 탐색**: Neo4j 기반 고속 그래프 쿼리
4. **교육 현장 맞춤형**: 교사/학생/연구자별 맞춤 뷰 제공
5. **데이터 무결성**: 순환 참조 0, 고립 노드 0의 완벽한 구조

---

## 📅 예상 개발 일정

- **Week 1**: 메인 대시보드 + 그래프 탐색기
- **Week 2**: 학습 경로 + 성취수준 분석
- **Week 3**: 쿼리 인터페이스 + AI 인사이트
- **Week 4**: 테스트 + 최적화 + 배포

---

*문서 작성일: 2024-12-27*
*프로젝트: 2022 개정 수학과 교육과정 지식 그래프*