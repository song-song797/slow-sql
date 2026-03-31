#!/bin/bash

# 生产环境启动脚本（使用 uvicorn）

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "错误: .env文件不存在，请先配置环境变量"
    exit 1
fi

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 激活虚拟环境
source slow-sql/bin/activate

# 使用 uvicorn 启动（不使用 --reload）
nohup python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 10800 \
    --workers 1 \
    --log-level info \
    --access-log \
    > logs/app.log 2>&1 &

echo "服务已启动，PID: $!"
echo $! > app.pid