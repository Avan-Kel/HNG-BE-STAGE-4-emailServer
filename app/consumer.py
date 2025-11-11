import os
import asyncio
import json
import httpx
from aio_pika import IncomingMessage
from email.message import EmailMessage
import aiosmtplib
from dotenv import load_dotenv

from .circuit_breaker import CircuitBreaker

load_dotenv()

# RabbitMQ config
RABBITMQ_URL = f"amqp://{os.getenv('RABBITMQ_USER')}:{os.getenv('RABBITMQ_PASS')}@{os.getenv('RABBITMQ_HOST')}:{os.getenv('RABBITMQ_PORT')}/"
QUEUE_NAME = os.getenv("RABBITMQ_QUEUE")

# SMTP config
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Template Service URL
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")

# Circuit breaker for email sending
circuit = CircuitBreaker(failure_threshold=5, recovery_time=30)

# -------------------------
# Helper functions
# -------------------------
async def send_email(to_email: str, subject: str, body: str):
    if not circuit.allow_request():
        print(f"Circuit open: skipping email to {to_email}")
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
        print(f"Email sent to {to_email}")
    except Exception as e:
        circuit.record_failure()
        print(f"Error sending email: {e}")

async def fetch_template(template_code: str) -> str:
    """Fetch template body from Template Service"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{TEMPLATE_SERVICE_URL}/templates/{template_code}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("body", "")
        except Exception as e:
            print(f"Failed to fetch template {template_code}: {e}")
            return ""  # fallback: empty template

def render_template(template_body: str, variables: dict) -> str:
    """Render template variables: {{var}}"""
    for key, value in variables.items():
        template_body = template_body.replace(f"{{{{{key}}}}}", str(value))
    return template_body

# -------------------------
# Consumer function
# -------------------------
async def on_message(message: IncomingMessage):
    async with message.process():
        data = message.body.decode()
        email_data = json.loads(data)

        template_body = await fetch_template(email_data["template_code"])
        email_body = render_template(template_body, email_data.get("variables", {}))
        subject = email_data.get("subject", "Notification")

        await send_email(email_data["email"], subject, email_body)

# -------------------------
# Start consumer
# -------------------------
async def start_consumer_in_background():
    """Start RabbitMQ consumer in the background (commented for testing without RabbitMQ)"""
    # try:
    #     from aio_pika import connect_robust
    #     connection = await connect_robust(RABBITMQ_URL)
    #     channel = await connection.channel()
    #     queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    #     await queue.consume(on_message)
    #     print(f"Email consumer listening on {QUEUE_NAME}...")
    #     await asyncio.Future()  # keep running
    # except Exception as e:
    #     print(f"[RabbitMQ] Connection failed: {e}")
    pass
