#!/bin/bash
# -*- coding: utf-8 -*-

# Claude Code 프로젝트 초기화 스크립트
# 수학 교육과정 지식 그래프 프로젝트

set -e

echo "🚀 수학 교육과정 프로젝트 초기화 시작..."

# 1. 환경 확인
echo "📋 환경 확인 중..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3가 필요합니다."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker가 필요합니다."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose가 필요합니다."; exit 1; }

# 2. Python 가상환경 설정
if [ ! -d "venv" ]; then
    echo "🐍 Python 가상환경 생성 중..."
    python3 -m venv venv
fi

echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 3. 의존성 설치
echo "📦 Python 패키지 설치 중..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt가 없습니다. knowledge_graph_project에서 확인합니다..."
    if [ -f "knowledge_graph_project/requirements.txt" ]; then
        pip install -r knowledge_graph_project/requirements.txt
    fi
fi

# 4. 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️ .env 파일이 없습니다. .env.example을 복사합니다..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 .env 파일이 생성되었습니다. API 키를 설정해주세요."
    fi
fi

# 5. Docker 서비스 상태 확인
echo "🐳 Docker 서비스 상태 확인..."
cd database 2>/dev/null || { echo "⚠️ database 폴더가 없습니다."; }

if [ -f "docker-compose.yml" ]; then
    docker-compose ps
else
    echo "⚠️ docker-compose.yml이 없습니다."
fi

cd ..

# 6. 데이터 파일 확인
echo "📊 데이터 파일 확인..."
if [ -d "data" ]; then
    total_csv=$(find data -name "*.csv" | wc -l)
    echo "✅ CSV 파일 $total_csv개 발견"
    
    # 주요 데이터 확인
    if [ -f "data/achievement_standards/achievement_standards_all.csv" ]; then
        standards_count=$(tail -n +2 data/achievement_standards/achievement_standards_all.csv | wc -l)
        echo "  - 성취기준: $standards_count개"
    fi
else
    echo "⚠️ data 폴더가 없습니다."
fi

# 7. Claude Code 설정 확인
echo "🤖 Claude Code 설정 확인..."
if [ -f ".claude/settings.json" ]; then
    echo "✅ Claude Code 설정 파일 존재"
fi

if [ -d ".claude/agents" ]; then
    agent_count=$(ls -1 .claude/agents/*.md 2>/dev/null | wc -l)
    echo "✅ 서브에이전트 $agent_count개 설정됨"
fi

if [ -d ".claude/commands" ]; then
    command_count=$(ls -1 .claude/commands/*.md 2>/dev/null | wc -l)
    echo "✅ 커스텀 명령어 $command_count개 설정됨"
fi

# 8. 프로젝트 정보 출력
echo ""
echo "════════════════════════════════════════════════════════"
echo "📚 수학 교육과정 지식 그래프 프로젝트"
echo "════════════════════════════════════════════════════════"
echo ""
echo "프로젝트 구조:"
echo "  • mathematics_curriculum_extraction/ - 교육과정 데이터"
echo "  • knowledge_graph_project/ - AI 파이프라인"
echo ""
echo "다음 명령어를 사용할 수 있습니다:"
echo "  /init-database    - 데이터베이스 초기화"
echo "  /validate-data    - 데이터 품질 검증"
echo "  /run-pipeline     - AI 파이프라인 실행"
echo "  /analyze-graph    - 지식 그래프 분석"
echo "  /run-tests        - 테스트 실행"
echo ""
echo "서브에이전트:"
echo "  • curriculum-analyst     - 교육과정 분석"
echo "  • database-architect     - DB 설계/최적화"
echo "  • ai-pipeline-engineer   - AI 파이프라인"
echo "  • knowledge-graph-specialist - 그래프 구축"
echo "  • python-data-engineer   - 데이터 처리"
echo "  • test-quality-engineer  - 품질 보증"
echo "  • devops-docker-specialist - Docker 관리"
echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ 초기화 완료! Claude Code에서 작업을 시작하세요."
echo "════════════════════════════════════════════════════════"