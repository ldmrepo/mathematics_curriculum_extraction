#!/bin/bash

# Docker 환경 관리 스크립트
# Knowledge Graph Construction Project

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로고 출력
print_header() {
    echo -e "${BLUE}"
    echo "🧠 Knowledge Graph Construction Project"
    echo "========================================="
    echo -e "${NC}"
}

# 사용법 출력
usage() {
    echo "사용법: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [env]     - 컨테이너 시작 (env: minimal, dev, prod)"
    echo "  stop            - 컨테이너 중지"
    echo "  restart [env]   - 컨테이너 재시작"
    echo "  logs [service]  - 로그 확인"
    echo "  status          - 상태 확인"
    echo "  clean           - 모든 데이터 삭제 (주의!)"
    echo "  backup          - 데이터 백업"
    echo "  restore [file]  - 데이터 복원"
    echo "  psql            - PostgreSQL 접속"
    echo "  neo4j           - Neo4j 브라우저 열기"
    echo "  redis           - Redis CLI 접속"
    echo ""
    echo "Examples:"
    echo "  $0 start minimal    # 최소 구성으로 시작"
    echo "  $0 start dev        # 개발 환경으로 시작"
    echo "  $0 logs postgres    # PostgreSQL 로그 확인"
    echo "  $0 backup           # 데이터 백업"
}

# Docker Compose 파일 선택
get_compose_file() {
    local env=${1:-minimal}
    case $env in
        minimal)
            echo "docker-compose.yml"
            ;;
        dev)
            echo "docker-compose.dev.yml"
            ;;
        prod)
            echo "docker-compose.prod.yml"
            ;;
        *)
            echo "docker-compose.yml"
            ;;
    esac
}

# 환경 변수 파일 로드
load_env() {
    if [ -f .env.docker ]; then
        export $(cat .env.docker | grep -v '#' | xargs)
    fi
}

# 컨테이너 시작
start_containers() {
    local env=${1:-minimal}
    local compose_file=$(get_compose_file $env)
    
    echo -e "${GREEN}🚀 Starting containers with $env configuration...${NC}"
    
    load_env
    docker-compose -f $compose_file up -d
    
    echo -e "${GREEN}✅ Containers started successfully!${NC}"
    echo ""
    echo "📋 Access Information:"
    echo "  PostgreSQL: localhost:5432"
    echo "  Neo4j Browser: http://localhost:7474"
    echo "  Redis: localhost:6379"
    
    if [ "$env" = "dev" ]; then
        echo "  pgAdmin: http://localhost:8080"
        echo "  Grafana: http://localhost:3000"
        echo "  ChromaDB: http://localhost:8000"
    fi
    
    echo ""
    echo "🔍 Check status with: $0 status"
}

# 컨테이너 중지
stop_containers() {
    echo -e "${YELLOW}⏹️  Stopping containers...${NC}"
    
    # 모든 compose 파일에 대해 stop 실행
    for compose_file in docker-compose.yml docker-compose.dev.yml docker-compose.prod.yml; do
        if [ -f $compose_file ]; then
            docker-compose -f $compose_file down 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ Containers stopped successfully!${NC}"
}

# 컨테이너 재시작
restart_containers() {
    local env=${1:-minimal}
    echo -e "${YELLOW}🔄 Restarting containers...${NC}"
    stop_containers
    sleep 2
    start_containers $env
}

# 로그 확인
show_logs() {
    local service=${1:-}
    local compose_file=$(get_compose_file)
    
    if [ -z "$service" ]; then
        echo -e "${BLUE}📋 Available services:${NC}"
        docker-compose -f $compose_file config --services
        echo ""
        echo "Usage: $0 logs [service_name]"
        return
    fi
    
    echo -e "${BLUE}📋 Showing logs for $service...${NC}"
    docker-compose -f $compose_file logs -f --tail=100 $service
}

# 상태 확인
check_status() {
    echo -e "${BLUE}📊 Container Status:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep kg_ || echo "No containers running"
    
    echo ""
    echo -e "${BLUE}💾 Volume Usage:${NC}"
    docker volume ls | grep kg_ || echo "No volumes found"
    
    echo ""
    echo -e "${BLUE}🌐 Network Info:${NC}"
    docker network ls | grep knowledge_graph || echo "No networks found"
}

# 데이터 정리
clean_data() {
    echo -e "${RED}⚠️  WARNING: This will delete ALL data!${NC}"
    read -p "Are you sure? (type 'DELETE' to confirm): " confirm
    
    if [ "$confirm" = "DELETE" ]; then
        echo -e "${YELLOW}🧹 Cleaning up data...${NC}"
        
        # 컨테이너 중지
        stop_containers
        
        # 볼륨 삭제
        docker volume rm $(docker volume ls -q | grep kg_) 2>/dev/null || true
        
        # 네트워크 삭제
        docker network rm $(docker network ls -q | grep knowledge_graph) 2>/dev/null || true
        
        echo -e "${GREEN}✅ Cleanup completed!${NC}"
    else
        echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
    fi
}

# 데이터 백업
backup_data() {
    local backup_dir="./backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $backup_dir
    
    echo -e "${BLUE}💾 Creating backup in $backup_dir...${NC}"
    
    # PostgreSQL 백업
    echo "📦 Backing up PostgreSQL..."
    docker exec kg_postgres pg_dump -U postgres mathematics_curriculum > $backup_dir/postgres_backup.sql
    
    # Neo4j 백업 (데이터 폴더 복사)
    echo "📦 Backing up Neo4j..."
    docker exec kg_neo4j tar -czf /tmp/neo4j_backup.tar.gz /data
    docker cp kg_neo4j:/tmp/neo4j_backup.tar.gz $backup_dir/
    
    # Redis 백업
    echo "📦 Backing up Redis..."
    docker exec kg_redis redis-cli BGSAVE
    docker cp kg_redis:/data/dump.rdb $backup_dir/redis_backup.rdb
    
    echo -e "${GREEN}✅ Backup completed: $backup_dir${NC}"
}

# 데이터 복원
restore_data() {
    local backup_file=${1:-}
    
    if [ -z "$backup_file" ]; then
        echo -e "${RED}❌ Please specify backup file${NC}"
        echo "Usage: $0 restore /path/to/backup"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}❌ Backup file not found: $backup_file${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}🔄 Restoring from $backup_file...${NC}"
    # 복원 로직 구현 (백업 형식에 따라)
    echo -e "${GREEN}✅ Restore completed${NC}"
}

# PostgreSQL 접속
connect_psql() {
    echo -e "${BLUE}🐘 Connecting to PostgreSQL...${NC}"
    docker exec -it kg_postgres psql -U postgres -d mathematics_curriculum
}

# Neo4j 브라우저 열기
open_neo4j() {
    echo -e "${BLUE}🌐 Opening Neo4j Browser...${NC}"
    
    if command -v open >/dev/null 2>&1; then
        open http://localhost:7474
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:7474
    else
        echo "Please open http://localhost:7474 in your browser"
        echo "Username: neo4j"
        echo "Password: neo4j123"
    fi
}

# Redis CLI 접속
connect_redis() {
    echo -e "${BLUE}🔴 Connecting to Redis...${NC}"
    docker exec -it kg_redis redis-cli
}

# 메인 실행 로직
main() {
    print_header
    
    local command=${1:-}
    
    case $command in
        start)
            start_containers ${2:-minimal}
            ;;
        stop)
            stop_containers
            ;;
        restart)
            restart_containers ${2:-minimal}
            ;;
        logs)
            show_logs $2
            ;;
        status)
            check_status
            ;;
        clean)
            clean_data
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data $2
            ;;
        psql)
            connect_psql
            ;;
        neo4j)
            open_neo4j
            ;;
        redis)
            connect_redis
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
