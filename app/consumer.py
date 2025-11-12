import os
import asyncio
import json
import httpx
from aio_pika import IncomingMessage, connect_robust
from email.message import EmailMessage
import aiosmtplib
from dotenv import load_dotenv
import logging

from .circuit_breaker import CircuitBreaker

load_dotenv()

# ✅ Logging setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/email-service.log",
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

# RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE", "email.notifications.queue")

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Template service
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")

# Circuit breaker
circuit = CircuitBreaker(failure_threshold=5, recovery_time=30)


async def send_email(to_email: str, subject: str, body: str):
    if not circuit.allow_request():
        logging.warning(f"CIRCUIT OPEN: Email skipped for {to_email}")
        return

    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=587,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS,
        )
        circuit.record_success()
        logging.info(f"✅ Email sent to {to_email}")

    except Exception as e:
        circuit.record_failure()
        logging.error(f"❌ Error sending email to {to_email}: {e}")


async def fetch_template(template_code: str) -> str:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{template_code}")
            resp.raise_for_status()
            data = resp.json()

            logging.info(f"✅ Template fetched: {template_code}")
            return data.get("body", "")

        except Exception as e:
            logging.error(f"❌ Failed to fetch template {template_code}: {e}")
            return ""


def render_template(template_body: str, variables: dict) -> str:
    for key, value in variables.items():
        template_body = template_body.replace(f"{{{{{key}}}}}", str(value))
    return template_body


async def on_message(message: IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())

        logging.info(f"📩 Received queue message: {data}")

        template_body = await fetch_template(data["template_code"])
        email_body = render_template(template_body, data.get("variables", {}))
        subject = data.get("subject", "Notification")

        await send_email(data["email"], subject, email_body)


async def start_consumer_in_background():
    try:
        connection = await connect_robust(RABBITMQ_URL, ssl=True)
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        await queue.consume(on_message)
        logging.info(f"📨 Consumer listening on queue: {QUEUE_NAME}")

        await asyncio.Future()

    except Exception as e:
        logging.error(f"❌ RabbitMQ connection failed: {e}")
