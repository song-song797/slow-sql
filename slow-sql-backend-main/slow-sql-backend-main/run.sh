#!/bin/bash

# 启动Slow SQL Analysis API服务

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "警告: .env文件不存在，请从.env.example复制并配置"
    echo "cp .env.example .env"
fi

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 尝试激活 conda 环境 (如果 conda 在路径中)
if command -v conda &> /dev/null; then
    # 这一步是为了让脚本能使用 conda activate
    eval "$(conda shell.bash hook)"
    conda activate slow-sql 2>/dev/null || echo "无法激活 'slow-sql' 环境，尝试直接运行..."
fi

# 使用 python -m uvicorn 启动，确保使用当前环境的包
# 注意：必须使用 python -m uvicorn 而不是直接使用 uvicorn 命令
# 这样可以确保使用conda环境中的Python和包，而不是系统Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 10800
