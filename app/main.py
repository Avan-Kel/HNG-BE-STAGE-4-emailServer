import os
from fastapi import FastAPI, HTTPException
import pika
import json
import asyncio
import uuid
import ssl
import logging

from .consumer import start_consumer_in_background
from .models import NotificationRequest, TestEmailRequest

# ✅ Logging setup
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/email-service.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

app = FastAPI(title="Email Service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE", "email.queue")


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_consumer_in_background())
    logging.info("✅ Consumer started")


@app.get("/")
def root():
    return {"message": "Email Service is running successfully"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/notifications/enqueue")
def enqueue_notification(payload: NotificationRequest):
    try:
        params = pika.URLParameters(RABBITMQ_URL)

        context = ssl.create_default_context()
        params.ssl_options = pika.SSLOptions(context)

        conn = pika.BlockingConnection(params)
        ch = conn.channel()

        ch.queue_declare(queue=QUEUE_NAME, durable=True)

        ch.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(payload.dict()),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()

        logging.info(f"📤 Enqueued notification: {payload.json()}")
        return {"success": True, "message": "Notification enqueued successfully"}

    except Exception as e:
        logging.error(f"❌ Failed to enqueue notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enqueue notification: {str(e)}")


@app.post("/enqueue-test-email")
def enqueue_test_email(payload: TestEmailRequest):
    try:
        request_id = str(uuid.uuid4())

        notification_payload = {
            "request_id": request_id,
            "notification_type": "email",
            "email": payload.email,
            "template_code": payload.template_code,
            "variables": payload.variables,
            "priority": payload.priority,
        }

        params = pika.URLParameters(RABBITMQ_URL)

        context = ssl.create_default_context()
        params.ssl_options = pika.SSLOptions(context)

        conn = pika.BlockingConnection(params)
        ch = conn.channel()

        ch.queue_declare(queue=QUEUE_NAME, durable=True)

        ch.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=json.dumps(notification_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()

        logging.info(f"📤 Test email queued: {notification_payload}")
        return {"success": True, "message": "Test email enqueued", "data": notification_payload}

    except Exception as e:
        logging.error(f"❌ Test email enqueue failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# LOGS API ENDPOINT
@app.get("/api/v1/logs")
def get_logs(limit: int = 100):
    try:
        if not os.path.exists(LOG_FILE):
            return {"logs": []}

        with open(LOG_FILE, "r") as f:
            lines = f.readlines()

        # return only last N lines
        last_lines = lines[-limit:]

        return {"count": len(last_lines), "logs": last_lines}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
