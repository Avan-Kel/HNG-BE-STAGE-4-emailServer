from fastapi import FastAPI, HTTPException
import os
import pika
import json
import asyncio
import uuid

from .consumer import start_consumer_in_background
from .models import NotificationRequest, TestEmailRequest

app = FastAPI(title="Email Service")

@app.on_event("startup")
async def on_startup():
    # Start the RabbitMQ consumer in the background
    # asyncio.create_task(start_consumer_in_background())
    pass

@app.get("/")
def root():
    return {"message": "Email Service is running successfully"}

@app.get("/health")
def health():
    return {"status": "ok"}

# @app.post("/api/v1/notifications/enqueue")
# def enqueue_notification(payload: NotificationRequest):
#     try:
#         rabbit_url = f"amqp://{os.getenv('RABBITMQ_USER')}:{os.getenv('RABBITMQ_PASS')}@{os.getenv('RABBITMQ_HOST')}:{os.getenv('RABBITMQ_PORT')}/"
#         exchange = os.getenv("RABBITMQ_EXCHANGE", "notifications.direct")
#         queue = os.getenv("RABBITMQ_QUEUE", "email.notifications.queue")

#         params = pika.URLParameters(rabbit_url)
#         conn = pika.BlockingConnection(params)
#         ch = conn.channel()

#         # Declare exchange & queue
#         ch.exchange_declare(exchange=exchange, exchange_type="direct", durable=True)
#         ch.queue_declare(queue=queue, durable=True)
#         ch.queue_bind(exchange=exchange, queue=queue, routing_key="email")

#         # Publish message
#         msg = json.dumps(payload.dict())
#         ch.basic_publish(
#             exchange=exchange,
#             routing_key="email",
#             body=msg,
#             properties=pika.BasicProperties(delivery_mode=2)
#         )
#         conn.close()

#         return {"success": True, "message": "Notification enqueued successfully", "data": payload.dict()}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to enqueue notification: {e}")



@app.post("/api/v1/notifications/enqueue")
def enqueue_notification(payload: NotificationRequest):
    # For testing without RabbitMQ
    return {
        "success": True,
        "message": "Notification enqueued successfully (mocked)",
        "data": payload.dict()
    }


@app.post("/enqueue-test-email")
def enqueue_test_email(payload: TestEmailRequest):
    try:
        request_id = str(uuid.uuid4())

        notification_payload = {
            "request_id": request_id,
            "notification_type": "email",
            "user_id": None,
            "email": payload.email,
            "template_code": payload.template_code,
            "variables": payload.variables,
            "priority": payload.priority,
            "metadata": payload.metadata,
        }

        rabbit_url = f"amqp://{os.getenv('RABBITMQ_USER')}:{os.getenv('RABBITMQ_PASS')}@{os.getenv('RABBITMQ_HOST')}:{os.getenv('RABBITMQ_PORT')}/"
        queue_name = os.getenv("RABBITMQ_QUEUE", "email.notifications.queue")
        params = pika.URLParameters(rabbit_url)
        conn = pika.BlockingConnection(params)
        ch = conn.channel()

        ch.queue_declare(queue=queue_name, durable=True)

        ch.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(notification_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()

        return {"success": True, "message": "Test email enqueued successfully", "data": notification_payload}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue test email: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Render will provide $PORT
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
