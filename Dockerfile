FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 收集静态文件（使用临时SECRET_KEY，避免构建时需要数据库）
RUN SECRET_KEY="build-time-secret-key-not-for-production" \
    DEBUG="False" \
    DATABASE_URL="" \
    python manage.py collectstatic --noinput || echo "collectstatic skipped"

# 创建数据目录
RUN mkdir -p /app/knowledge_base/chroma_db /app/media /app/logs

# 暴露端口
EXPOSE 8000

# 启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
