#!/bin/bash
# Render构建脚本
set -e

echo "=== 安装依赖 ==="
pip install -r requirements.txt

echo "=== 收集静态文件 ==="
python manage.py collectstatic --noinput

echo "=== 数据库迁移 ==="
python manage.py migrate

echo "=== 初始化数据 ==="
python data/init_fuzhou_data.py || echo "数据初始化跳过（已存在）"
python data/enhance_data.py || echo "数据增强跳过（已存在）"

echo "=== 构建知识库 ==="
python knowledge_base/build_knowledge_base.py || echo "知识库构建跳过（已存在或依赖缺失）"

echo "=== 构建完成 ==="
