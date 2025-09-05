#!/bin/bash

# GitHub Discussions 自动化分析服务部署脚本
# 支持多种部署方式：Docker Compose、systemd服务、开发模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "${DEBUG}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
GitHub Discussions 自动化分析服务部署脚本

用法: $0 [选项] [命令]

命令:
  docker          使用Docker Compose部署
  systemd         创建systemd服务
  dev             开发模式运行
  stop            停止服务
  restart         重启服务
  status          查看服务状态
  logs            查看日志
  update          更新服务
  clean           清理资源

选项:
  -h, --help      显示帮助信息
  -v, --verbose   详细输出
  -c, --config    指定配置文件路径
  --env-file      指定环境变量文件路径

示例:
  $0 docker                    # 使用Docker Compose部署
  $0 systemd                   # 创建systemd服务
  $0 dev                       # 开发模式运行
  $0 logs                      # 查看日志
  $0 --config /path/to/config docker  # 指定配置文件部署

EOF
}

# 检查依赖
check_dependencies() {
    local deps=("$@")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "缺少依赖: ${missing[*]}"
        log_info "请安装缺少的依赖后重试"
        exit 1
    fi
}

# 检查环境变量文件
check_env_file() {
    local env_file="${ENV_FILE:-env.example}"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "环境变量文件不存在: $env_file"
        log_info "请复制 env.example 到 .env 并配置必要的环境变量"
        exit 1
    fi
    
    # 检查关键环境变量
    source "$env_file"
    
    local required_vars=("GITHUB_TOKEN" "GITHUB_ORG" "GITHUB_REPO" "GLM_API_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必需的环境变量: ${missing_vars[*]}"
        log_info "请在 $env_file 中配置这些变量"
        exit 1
    fi
    
    log_info "环境变量检查通过"
}

# Docker Compose部署
deploy_docker() {
    log_info "开始Docker Compose部署..."
    
    check_dependencies "docker" "docker-compose"
    check_env_file
    
    # 创建必要的目录
    mkdir -p logs data
    
    # 构建和启动服务
    log_info "构建Docker镜像..."
    docker-compose build
    
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_info "服务启动成功！"
        docker-compose ps
    else
        log_error "服务启动失败"
        docker-compose logs
        exit 1
    fi
}

# systemd服务部署
deploy_systemd() {
    log_info "开始创建systemd服务..."
    
    check_dependencies "python3" "pip"
    check_env_file
    
    local service_name="github-analyzer"
    local service_file="/etc/systemd/system/${service_name}.service"
    local working_dir="$(pwd)"
    local user="${USER}"
    
    # 安装Python依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    # 创建systemd服务文件
    log_info "创建systemd服务文件..."
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=GitHub Discussions 自动化分析服务
After=network.target

[Service]
Type=simple
User=${user}
WorkingDirectory=${working_dir}
Environment=PYTHONPATH=${working_dir}
EnvironmentFile=${working_dir}/.env
ExecStart=/usr/bin/python3 ${working_dir}/main_enhanced.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd配置
    sudo systemctl daemon-reload
    
    # 启用并启动服务
    sudo systemctl enable "$service_name"
    sudo systemctl start "$service_name"
    
    # 检查服务状态
    if sudo systemctl is-active --quiet "$service_name"; then
        log_info "systemd服务创建成功！"
        sudo systemctl status "$service_name"
    else
        log_error "systemd服务启动失败"
        sudo systemctl status "$service_name"
        exit 1
    fi
}

# 开发模式运行
run_dev() {
    log_info "开始开发模式运行..."
    
    check_dependencies "python3" "pip"
    check_env_file
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt
    
    # 设置环境变量
    export PYTHONPATH="$(pwd)"
    source "${ENV_FILE:-env.example}"
    
    # 运行服务
    log_info "启动分析服务..."
    python3 main_enhanced.py
}

# 停止服务
stop_service() {
    log_info "停止服务..."
    
    # 尝试停止Docker Compose服务
    if [[ -f "docker-compose.yml" ]] && docker-compose ps >/dev/null 2>&1; then
        log_info "停止Docker Compose服务..."
        docker-compose down
    fi
    
    # 尝试停止systemd服务
    if systemctl is-active --quiet github-analyzer 2>/dev/null; then
        log_info "停止systemd服务..."
        sudo systemctl stop github-analyzer
    fi
    
    log_info "服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    stop_service
    sleep 5
    
    # 根据现有配置重启相应服务
    if [[ -f "docker-compose.yml" ]]; then
        deploy_docker
    elif systemctl list-unit-files | grep -q github-analyzer; then
        sudo systemctl start github-analyzer
    else
        log_warn "未找到已配置的服务，请先进行部署"
    fi
}

# 查看服务状态
show_status() {
    log_info "查看服务状态..."
    
    # Docker状态
    if [[ -f "docker-compose.yml" ]]; then
        echo "=== Docker Compose 服务状态 ==="
        docker-compose ps 2>/dev/null || echo "Docker Compose服务未运行"
        echo
    fi
    
    # systemd状态
    if systemctl list-unit-files | grep -q github-analyzer; then
        echo "=== systemd 服务状态 ==="
        sudo systemctl status github-analyzer --no-pager
        echo
    fi
}

# 查看日志
show_logs() {
    log_info "查看服务日志..."
    
    # Docker日志
    if [[ -f "docker-compose.yml" ]] && docker-compose ps >/dev/null 2>&1; then
        echo "=== Docker 服务日志 ==="
        docker-compose logs -f --tail=100
        return
    fi
    
    # systemd日志
    if systemctl is-active --quiet github-analyzer 2>/dev/null; then
        echo "=== systemd 服务日志 ==="
        sudo journalctl -u github-analyzer -f --lines=100
        return
    fi
    
    # 本地日志文件
    if [[ -f "logs/analyzer.log" ]]; then
        echo "=== 本地日志文件 ==="
        tail -f logs/analyzer.log
        return
    fi
    
    log_warn "未找到可用的日志源"
}

# 更新服务
update_service() {
    log_info "更新服务..."
    
    # Git更新
    if [[ -d ".git" ]]; then
        log_info "更新代码..."
        git pull
    fi
    
    # 重新构建和重启
    if [[ -f "docker-compose.yml" ]]; then
        log_info "重新构建Docker镜像..."
        docker-compose build --no-cache
        docker-compose down
        docker-compose up -d
    elif systemctl list-unit-files | grep -q github-analyzer; then
        log_info "重新安装依赖..."
        pip install -r requirements.txt
        sudo systemctl restart github-analyzer
    fi
    
    log_info "服务更新完成"
}

# 清理资源
clean_resources() {
    log_info "清理资源..."
    
    # 停止服务
    stop_service
    
    # 清理Docker资源
    if command -v docker >/dev/null 2>&1; then
        log_info "清理Docker资源..."
        docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
        docker system prune -f
    fi
    
    # 删除systemd服务
    if systemctl list-unit-files | grep -q github-analyzer; then
        log_info "删除systemd服务..."
        sudo systemctl disable github-analyzer
        sudo rm -f /etc/systemd/system/github-analyzer.service
        sudo systemctl daemon-reload
    fi
    
    # 清理日志文件
    if [[ -d "logs" ]]; then
        log_info "清理日志文件..."
        rm -rf logs/*
    fi
    
    log_info "资源清理完成"
}

# 解析命令行参数
VERBOSE=false
CONFIG_FILE=""
ENV_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            DEBUG=true
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        docker|systemd|dev|stop|restart|status|logs|update|clean)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 设置默认命令
if [[ -z "${COMMAND:-}" ]]; then
    COMMAND="docker"
fi

# 执行命令
case "$COMMAND" in
    docker)
        deploy_docker
        ;;
    systemd)
        deploy_systemd
        ;;
    dev)
        run_dev
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    update)
        update_service
        ;;
    clean)
        clean_resources
        ;;
    *)
        log_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac
