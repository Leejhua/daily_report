# GitHub Discussions 自动化分析服务 Docker 镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码和配置文件
COPY src/ ./src/
COPY config/ ./config/
COPY env.example ./
COPY feishu_mapping.json ./

# 创建必要的目录
RUN mkdir -p logs data reports .trae/documents tests/output tests/results

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置目录权限
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app && \
    chmod -R 777 logs data reports .trae/documents tests/output tests/results

USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app'); from src.config import Config; config = Config(); print('Health check passed')" || exit 1

# 暴露端口（如果需要的话）
# EXPOSE 8000

# 启动命令
CMD ["python", "-u", "main_enhanced.py"]
