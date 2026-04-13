FROM python:3.10-slim

WORKDIR /app
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/checkpoints /var/log/postgresql /var/log/udal

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:10801/health >/dev/null || exit 1

CMD ["python", "main.py"]
