# 多阶段构建优化版本
FROM reg.un-net.com/python/python:3.10-slim as builder

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN rm -rf /etc/apt/sources.list.d/* /etc/apt/sources.list && \
    mkdir -p /etc/apt/sources.list.d

# 彻底清理旧的 APT 列表缓存（防止复用）
RUN rm -rf /var/lib/apt/lists/*

# 创建 /etc/apt/sources.list（使用清华源）
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 设置 pip 镜像源并安装 Python 依赖
RUN pip install --upgrade pip && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 复制静态文件（Swagger UI 等）
COPY static/ ./static/

# 暴露端口
EXPOSE 10800

# 定义环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动应用
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10800"]


