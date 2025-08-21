"""
Streamlit Dashboard for Knowledge Graph Construction Project
"""
import streamlit as st
import json
import os
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys

# Add src to path
sys.path.append('src')

from main import KnowledgeGraphOrchestrator

st.set_page_config(
    page_title="지식 그래프 구축 대시보드",
    page_icon="🧠",
    layout="wide"
)

class StreamlitDashboard:
    """Streamlit dashboard for the knowledge graph project"""
    
    def __init__(self):
        self.orchestrator = None
    
    def run(self):
        """Main dashboard interface"""
        st.title("🧠 지식 그래프 구축 프로젝트 대시보드")
        st.markdown("2025년 최신 AI 모델을 활용한 수학 교육과정 지식 그래프 구축")
        
        # Sidebar
        self._create_sidebar()
        
        # Main content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 프로젝트 개요", 
            "🚀 실행 제어", 
            "📈 진행 상황", 
            "🔍 결과 분석", 
            "📋 최종 보고서"
        ])
        
        with tab1:
            self._show_project_overview()
        
        with tab2:
            self._show_execution_control()
        
        with tab3:
            self._show_progress_monitoring()
        
        with tab4:
            self._show_results_analysis()
        
        with tab5:
            self._show_final_report()
    
    def _create_sidebar(self):
        """Create sidebar with navigation and status"""
        st.sidebar.title("📋 프로젝트 상태")
        
        # Check output files
        output_files = {
            "Phase 1": "output/phase1_foundation_design.json",
            "Phase 2": "output/phase2_relationship_extraction.json", 
            "Phase 3": "output/phase3_refinement_results.json",
            "Phase 4": "output/phase4_validation_results.json",
            "Final Report": "output/final_report.json"
        }
        
        for phase, file_path in output_files.items():
            if os.path.exists(file_path):
                st.sidebar.success(f"✅ {phase} 완료")
            else:
                st.sidebar.warning(f"⏳ {phase} 대기중")
        
        st.sidebar.markdown("---")
        
        # Quick stats if files exist
        if os.path.exists("output/final_report.json"):
            with open("output/final_report.json", 'r', encoding='utf-8') as f:
                report = json.load(f)
                
            total_cost = report.get('execution_summary', {}).get('total_cost', 0)
            st.sidebar.metric("총 비용", f"${total_cost:.2f}")
            
            phases_completed = report.get('execution_summary', {}).get('phases_completed', 0)
            st.sidebar.metric("완료된 단계", f"{phases_completed}/5")
    
    def _show_project_overview(self):
        """Show project overview"""
        st.header("📊 프로젝트 개요")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 프로젝트 목표")
            st.markdown("""
            - 한국 수학 교육과정의 지식 그래프 구축
            - 2025년 최신 AI 모델 활용 (GPT-5, Claude 4, Gemini 2.5)
            - 성취기준 간 관계 자동 추출 및 분석
            - 교육적 맥락을 고려한 지식 체계 구성
            """)
            
            st.subheader("📈 예상 성과")
            st.markdown("""
            - **1,024개** 노드 (성취기준 + 성취수준)
            - **3,000+** 관계 (선수학습, 유사성, 진행 등)
            - **80개** 커뮤니티 클러스터 (3단계 계층)
            - **95%+** 분류 정확도 목표
            """)
        
        with col2:
            st.subheader("🤖 AI 모델 활용 전략")
            
            # Model usage chart
            models_data = {
                'AI 모델': ['Gemini 2.5 Pro', 'GPT-5', 'Claude Sonnet 4', 'Claude Opus 4.1'],
                '활용 영역': ['구조 설계', '관계 추출', '세밀 분석', '최종 검증'],
                '예상 비용': [15, 50, 20, 50]
            }
            
            fig = px.bar(
                x=models_data['AI 모델'],
                y=models_data['예상 비용'],
                title="AI 모델별 예상 비용 ($)",
                color=models_data['예상 비용'],
                color_continuous_scale="viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📅 예상 일정")
            schedule_data = {
                '단계': ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Neo4j 구축'],
                '소요 시간': [0.5, 1.5, 1.0, 1.0, 0.5],
                '상태': ['대기', '대기', '대기', '대기', '대기']
            }
            
            df_schedule = pd.DataFrame(schedule_data)
            st.dataframe(df_schedule, use_container_width=True)
    
    def _show_execution_control(self):
        """Show execution control panel"""
        st.header("🚀 실행 제어")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("파이프라인 실행")
            
            # Execution options
            resume_from = st.selectbox(
                "시작할 단계 선택",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: f"Phase {x}",
                help="이전 단계 결과가 있는 경우 중간부터 시작 가능"
            )
            
            phase_only = st.selectbox(
                "특정 단계만 실행 (선택사항)",
                options=[None, 1, 2, 3, 4, 5],
                format_func=lambda x: "전체 파이프라인" if x is None else f"Phase {x}만",
                help="특정 단계만 실행하려면 선택"
            )
            
            # Configuration
            st.subheader("설정")
            
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                max_cost = st.number_input(
                    "최대 비용 한도 ($)",
                    min_value=50,
                    max_value=500,
                    value=200,
                    help="AI API 호출 비용 한도"
                )
                
                batch_size = st.number_input(
                    "배치 크기",
                    min_value=10,
                    max_value=100,
                    value=50,
                    help="관계 추출 시 배치 처리 크기"
                )
            
            with col_config2:
                use_caching = st.checkbox(
                    "프롬프트 캐싱 사용",
                    value=True,
                    help="비용 절감을 위한 캐싱 활성화"
                )
                
                create_neo4j = st.checkbox(
                    "Neo4j 그래프 생성",
                    value=True,
                    help="최종 결과를 Neo4j 데이터베이스에 저장"
                )
        
        with col2:
            st.subheader("빠른 실행")
            
            if st.button("🚀 전체 파이프라인 실행", type="primary"):
                st.info("파이프라인 실행을 시작합니다...")
                # Note: In real implementation, this would call the orchestrator
                st.warning("실제 구현에서는 비동기 실행이 필요합니다.")
            
            if st.button("🔄 상태 새로고침"):
                st.rerun()
            
            if st.button("📊 로그 보기"):
                self._show_logs()
            
            if st.button("💾 결과 다운로드"):
                self._download_results()
    
    def _show_progress_monitoring(self):
        """Show progress monitoring"""
        st.header("📈 진행 상황")
        
        # Progress overview
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate progress from existing files
        completed_phases = 0
        total_phases = 5
        
        phase_files = [
            "output/phase1_foundation_design.json",
            "output/phase2_relationship_extraction.json",
            "output/phase3_refinement_results.json", 
            "output/phase4_validation_results.json",
            "output/final_report.json"
        ]
        
        for file_path in phase_files:
            if os.path.exists(file_path):
                completed_phases += 1
        
        progress_percent = (completed_phases / total_phases) * 100
        
        with col1:
            st.metric("전체 진행률", f"{progress_percent:.1f}%")
        
        with col2:
            st.metric("완료 단계", f"{completed_phases}/{total_phases}")
        
        with col3:
            if os.path.exists("output/final_report.json"):
                with open("output/final_report.json", 'r', encoding='utf-8') as f:
                    report = json.load(f)
                cost = report.get('execution_summary', {}).get('total_cost', 0)
                st.metric("누적 비용", f"${cost:.2f}")
            else:
                st.metric("누적 비용", "$0.00")
        
        with col4:
            if completed_phases > 0:
                st.metric("상태", "진행중" if completed_phases < total_phases else "완료")
            else:
                st.metric("상태", "대기중")
        
        # Progress bar
        st.progress(progress_percent / 100)
        
        # Phase details
        st.subheader("단계별 상세 진행률")
        
        phase_details = [
            {"phase": "Phase 1", "name": "기반 구조 설계", "file": "output/phase1_foundation_design.json"},
            {"phase": "Phase 2", "name": "관계 추출", "file": "output/phase2_relationship_extraction.json"},
            {"phase": "Phase 3", "name": "고도화 정제", "file": "output/phase3_refinement_results.json"},
            {"phase": "Phase 4", "name": "검증 최적화", "file": "output/phase4_validation_results.json"},
            {"phase": "Phase 5", "name": "최종 보고서", "file": "output/final_report.json"}
        ]
        
        for detail in phase_details:
            col_phase, col_status, col_time = st.columns([2, 1, 2])
            
            with col_phase:
                st.text(f"{detail['phase']}: {detail['name']}")
            
            with col_status:
                if os.path.exists(detail['file']):
                    st.success("완료")
                else:
                    st.warning("대기")
            
            with col_time:
                if os.path.exists(detail['file']):
                    mod_time = os.path.getmtime(detail['file'])
                    st.text(datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M"))
                else:
                    st.text("-")
    
    def _show_results_analysis(self):
        """Show results analysis"""
        st.header("🔍 결과 분석")
        
        # Check if results exist
        if not os.path.exists("output/final_report.json"):
            st.warning("아직 결과가 없습니다. 파이프라인을 실행해주세요.")
            return
        
        # Load results
        with open("output/final_report.json", 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # Quality assessment
        st.subheader("📊 품질 평가")
        
        quality_data = report.get('quality_assessment', {})
        if quality_data and quality_data != {'status': 'not_available'}:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                final_grade = quality_data.get('final_grade', 'N/A')
                st.metric("최종 등급", final_grade)
            
            with col2:
                total_score = quality_data.get('total_score', 0.0)
                st.metric("총점", f"{total_score:.2f}/1.0")
            
            with col3:
                readiness = quality_data.get('commercialization_readiness', 'unknown')
                readiness_map = {
                    'ready': '준비완료',
                    'needs_improvement': '개선필요', 
                    'not_ready': '미준비'
                }
                st.metric("상용화 준비도", readiness_map.get(readiness, readiness))
        
        # Usage statistics
        st.subheader("💰 비용 분석")
        
        usage_stats = report.get('usage_statistics', {})
        if usage_stats:
            # Model costs
            models_data = []
            for model_name, stats in usage_stats.get('models', {}).items():
                models_data.append({
                    'Model': model_name,
                    'Cost': stats.get('total_cost', 0),
                    'Input Tokens': stats.get('input_tokens', 0),
                    'Output Tokens': stats.get('output_tokens', 0)
                })
            
            if models_data:
                df_models = pd.DataFrame(models_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.pie(
                        df_models, 
                        values='Cost', 
                        names='Model',
                        title="모델별 비용 분포"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(
                        df_models, 
                        x='Model', 
                        y=['Input Tokens', 'Output Tokens'],
                        title="모델별 토큰 사용량",
                        barmode='stack'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Graph statistics
        st.subheader("🔗 그래프 통계")
        
        graph_stats = report.get('graph_statistics', {})
        if graph_stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.text("노드 통계")
                nodes = graph_stats.get('nodes', {})
                for node_type, count in nodes.items():
                    st.metric(node_type, count)
            
            with col2:
                st.text("관계 통계")
                relationships = graph_stats.get('relationships', {})
                for rel_type, count in relationships.items():
                    st.metric(rel_type, count)
    
    def _show_final_report(self):
        """Show final report"""
        st.header("📋 최종 보고서")
        
        if not os.path.exists("output/final_report.json"):
            st.warning("최종 보고서가 아직 생성되지 않았습니다.")
            return
        
        # Load report
        with open("output/final_report.json", 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # Executive summary
        if os.path.exists("output/executive_summary.md"):
            st.subheader("📝 경영진 요약")
            with open("output/executive_summary.md", 'r', encoding='utf-8') as f:
                summary = f.read()
            st.markdown(summary)
        
        # Key achievements
        st.subheader("🏆 주요 성과")
        quality_assessment = report.get('quality_assessment', {})
        achievements = quality_assessment.get('key_achievements', [])
        
        if achievements:
            for achievement in achievements:
                st.success(f"✅ {achievement}")
        
        # Recommendations
        st.subheader("💡 권장사항")
        recommendations = report.get('recommendations', [])
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.info(f"{i}. {rec}")
        
        # Next steps
        st.subheader("🚀 다음 단계")
        next_steps = report.get('next_steps', [])
        
        if next_steps:
            for i, step in enumerate(next_steps, 1):
                st.warning(f"{i}. {step}")
        
        # Download options
        st.subheader("📥 다운로드")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 전체 보고서 JSON"):
                st.download_button(
                    label="다운로드",
                    data=json.dumps(report, ensure_ascii=False, indent=2),
                    file_name="final_report.json",
                    mime="application/json"
                )
        
        with col2:
            if os.path.exists("output/executive_summary.md"):
                with open("output/executive_summary.md", 'r', encoding='utf-8') as f:
                    summary_content = f.read()
                
                st.download_button(
                    label="📝 요약 보고서 MD",
                    data=summary_content,
                    file_name="executive_summary.md",
                    mime="text/markdown"
                )
        
        with col3:
            if os.path.exists("output/graph_statistics.json"):
                with open("output/graph_statistics.json", 'r', encoding='utf-8') as f:
                    graph_data = f.read()
                
                st.download_button(
                    label="📈 그래프 통계 JSON",
                    data=graph_data,
                    file_name="graph_statistics.json",
                    mime="application/json"
                )
    
    def _show_logs(self):
        """Show logs in modal"""
        log_files = [f for f in os.listdir("logs") if f.endswith(".log")] if os.path.exists("logs") else []
        
        if log_files:
            latest_log = max(log_files, key=lambda x: os.path.getmtime(f"logs/{x}"))
            with open(f"logs/{latest_log}", 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            st.text_area("최근 로그", log_content, height=300)
        else:
            st.info("로그 파일이 없습니다.")
    
    def _download_results(self):
        """Prepare results for download"""
        st.info("결과 파일들을 압축하여 다운로드 준비 중...")
        # In real implementation, create zip file of all outputs

# Main Streamlit app
def main():
    dashboard = StreamlitDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
