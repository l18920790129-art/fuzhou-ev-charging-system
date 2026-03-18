#!/bin/bash
set -e

echo "=== 福州充电桩智能选址系统启动 ==="

# 数据库迁移
echo ">>> 执行数据库迁移..."
python manage.py migrate --noinput

# 初始化数据（如果数据库为空）
echo ">>> 检查并初始化数据..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuzhou_ev_charging.settings')
django.setup()
from maps.models import POIData
if POIData.objects.count() == 0:
    print('数据库为空，开始初始化...')
    import subprocess
    subprocess.run(['python', 'data/init_fuzhou_data.py'], check=True)
    subprocess.run(['python', 'data/enhance_data.py'], check=True)
    print('数据初始化完成')
else:
    print(f'数据库已有 {POIData.objects.count()} 条POI数据，跳过初始化')
"

# 构建知识库（如果不存在）
echo ">>> 检查知识库..."
python -c "
import os
chroma_dir = os.environ.get('CHROMA_PERSIST_DIR', 'knowledge_base/chroma_db')
if not os.path.exists(chroma_dir) or not os.listdir(chroma_dir):
    print('知识库不存在，开始构建...')
    import subprocess
    subprocess.run(['python', 'knowledge_base/build_knowledge_base.py'], check=True)
    print('知识库构建完成')
else:
    print('知识库已存在，跳过构建')
" || echo "知识库检查跳过"

# 启动服务
echo ">>> 启动 Gunicorn 服务..."
exec gunicorn fuzhou_ev_charging.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
