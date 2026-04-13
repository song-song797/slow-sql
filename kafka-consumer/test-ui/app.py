"""Kafka 消息测试服务 - FastAPI 应用"""

import json
import logging

import re
import time
from datetime import datetime
from typing import Optional

from confluent_kafka import Producer
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("test-ui")

app = FastAPI(title="Kafka 消息测试工具")

# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# Kafka 配置
KAFKA_SERVERS = "172.20.40.166:9094"
producer = Producer({
    "bootstrap.servers": KAFKA_SERVERS,
    "linger.ms": 50,
    "message.timeout.ms": 10000,
})

# UDAL 日志行匹配
UDAL_LINE_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<payload>\{.*\})$")


def delivery_report(err, msg):
    if err:
        logger.error(f"发送失败: {err}")
    else:
        logger.info(f"发送成功: topic={msg.topic()}, partition={msg.partition()}")


class SendMessage(BaseModel):
    topic: str
    message: str


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/send")
async def send_message(body: SendMessage):
    """发送消息到 Kafka"""
    try:
        value = body.message.encode("utf-8")
        producer.produce(body.topic, value=value, callback=delivery_report)
        producer.flush(timeout=10)
        return {"status": "ok", "topic": body.topic, "size": len(value)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


@app.post("/api/send-batch")
async def send_batch(request: Request):
    """批量发送多条消息"""
    data = await request.json()
    topic = data.get("topic")
    messages = data.get("messages", [])

    if not topic or not messages:
        return JSONResponse(status_code=400, content={"error": "topic 和 messages 必填"})

    success = 0
    errors = []
    for msg in messages:
        try:
            producer.produce(topic, value=json.dumps(msg, ensure_ascii=False).encode("utf-8"), callback=delivery_report)
            success += 1
        except Exception as e:
            errors.append(str(e))

    producer.flush(timeout=30)
    return {"status": "ok", "sent": success, "errors": errors}


@app.post("/api/send-raw")
async def send_raw_logs(request: Request):
    """粘贴原始日志发送，自动包装成 Kafka 消息格式"""
    data = await request.json()
    topic = data.get("topic")
    raw_text = data.get("raw_text", "")

    if not topic or not raw_text:
        return JSONResponse(status_code=400, content={"error": "topic 和 raw_text 必填"})

    lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
    if not lines:
        return JSONResponse(status_code=400, content={"error": "没有有效内容"})

    messages = []
    for line in lines:
        msg = _wrap_raw_line(line, topic)
        if msg:
            messages.append(msg)

    if not messages:
        return JSONResponse(status_code=400, content={"error": "没有可解析的日志行"})

    success = 0
    errors = []
    for msg in messages:
        try:
            producer.produce(topic, value=json.dumps(msg, ensure_ascii=False).encode("utf-8"), callback=delivery_report)
            success += 1
        except Exception as e:
            errors.append(str(e))

    producer.flush(timeout=30)
    return {"status": "ok", "sent": success, "total_lines": len(lines), "errors": errors}


@app.post("/api/upload-log")
async def upload_log_file(topic: str, file: UploadFile = File(...)):
    """上传日志文件，逐行解析发送到 Kafka"""
    if not topic:
        return JSONResponse(status_code=400, content={"error": "topic 必填"})

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    messages = []
    for line in lines:
        msg = _wrap_raw_line(line, topic)
        if msg:
            messages.append(msg)

    if not messages:
        return JSONResponse(status_code=400, content={
            "error": "没有可解析的日志行",
            "total_lines": len(lines),
        })

    success = 0
    errors = []
    for msg in messages:
        try:
            producer.produce(topic, value=json.dumps(msg, ensure_ascii=False).encode("utf-8"), callback=delivery_report)
            success += 1
        except Exception as e:
            errors.append(str(e))

    producer.flush(timeout=60)
    return {
        "status": "ok",
        "filename": file.filename,
        "total_lines": len(lines),
        "parsed": len(messages),
        "sent": success,
        "errors": errors,
    }


def _wrap_raw_line(line: str, topic: str) -> Optional[dict]:
    """将原始日志行包装成 Kafka 消息格式"""
    now = time.time()

    if topic == "log_push_pg":
        # PG 日志：直接包装原始行
        return {
            "raw_line": line,
            "source": "postgresql",
            "collected_at": now,
        }
    elif topic == "log_push_udal":
        # UDAL 日志：尝试解析 时间戳+JSON 格式
        match = UDAL_LINE_RE.match(line)
        if match:
            try:
                payload = json.loads(match.group("payload"))
                return {
                    "timestamp": match.group("ts"),
                    "payload": payload,
                    "source": "udal",
                    "collected_at": now,
                }
            except json.JSONDecodeError:
                pass
        # 如果不符合 UDAL 格式，也尝试包装
        return {
            "raw_line": line,
            "source": "udal",
            "collected_at": now,
        }
    return None


@app.get("/api/templates")
async def get_templates():
    """获取消息模板"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "pg": {
            "name": "PG 慢日志（duration+statement 同行）",
            "topic": "log_push_pg",
            "message": json.dumps({
                "raw_line": f"2026-04-08 10:30:00.123 CST [12345] user:csc, client:192.168.1.100(54321), database:cscdb LOG:  duration: 1500.456 ms  statement: SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC",
                "source": "postgresql",
                "collected_at": datetime.now().timestamp(),
            }, ensure_ascii=False, indent=2),
        },
        "pg_duration_only": {
            "name": "PG 慢日志（仅 duration）",
            "topic": "log_push_pg",
            "message": json.dumps({
                "raw_line": f"2026-04-08 10:30:00.123 CST [12345] user:csc, client:192.168.1.100(54321), database:cscdb LOG:  duration: 1500.456 ms",
                "source": "postgresql",
                "collected_at": datetime.now().timestamp(),
            }, ensure_ascii=False, indent=2),
        },
        "pg_statement_only": {
            "name": "PG 慢日志（仅 statement）",
            "topic": "log_push_pg",
            "message": json.dumps({
                "raw_line": f"2026-04-08 10:30:00.123 CST [12345] user:csc, client:192.168.1.100(54321), database:cscdb LOG:  statement: SELECT * FROM orders WHERE user_id = 123 ORDER BY created_at DESC",
                "source": "postgresql",
                "collected_at": datetime.now().timestamp(),
            }, ensure_ascii=False, indent=2),
        },
        "udal_request": {
            "name": "UDAL 审计日志（RECEIVE_REQUEST）",
            "topic": "log_push_udal",
            "message": json.dumps({
                "timestamp": now,
                "payload": {
                    "schema": "CUSDBX",
                    "requestId": 99999,
                    "eventType": "RECEIVE_REQUEST",
                    "user": "crmtest@192.168.1.100:54321",
                    "sql": "SELECT * FROM party_cert WHERE party_id = '110421635955' AND party_cert_id = '1346443'",
                },
                "source": "udal",
                "collected_at": datetime.now().timestamp(),
            }, ensure_ascii=False, indent=2),
        },
        "udal_end": {
            "name": "UDAL 审计日志（END_REQUEST，需与上面 requestId 一致）",
            "topic": "log_push_udal",
            "message": json.dumps({
                "timestamp": now,
                "payload": {
                    "requestId": 99999,
                    "eventType": "END_REQUEST",
                    "cost": 200,
                },
                "source": "udal",
                "collected_at": datetime.now().timestamp(),
            }, ensure_ascii=False, indent=2),
        },
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "kafka": KAFKA_SERVERS}
