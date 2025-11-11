*** Email Notification Service ***

A microservice responsible for delivering templated email notifications.
Designed for distributed systems with RabbitMQ, FastAPI, template rendering, and optional retry & DLQ (dead-letter queue) handling.

## Overview

The Email Service receives notification requests, renders templates with dynamic variables (e.g., {{name}}), and sends emails using SMTP or a third-party provider such as SendGrid/Mailgun/Gmail.


## Key Features

- Accept notification requests through REST API
- Publishes messages to RabbitMQ (when enabled)
- Background consumer to read messages and send emails
- Jinja2 template rendering ({{variable}} format)
- Retry and exponential backoff
- Dead-letter queue support
- Horizontal scaling – multiple workers can run in parallel
- Health check endpoint for monitoring


## Tech Stack
- Technology
- FastAPI
- RabbitMQ
- Jinja2
- SMTP
- Deployment	Render.com 


## RabbitMQ Not Available?
- Application runs in MOCK mode automatically.
- Notifications are accepted normally.
- They are printed to console instead of being published.


## Running Locally
1. Install dependencies
pip install -r requirements.txt

2. Run API
uvicorn app.main:app --reload --port 8001

API is available at:

http://localhost:8001
http://localhost:8001/docs

- API Endpoints
- Health Check

GET /health
Returns service status (used by Kubernetes / Render monitoring)

## Enqueue Notification (Mock or Live)

POST /api/v1/notifications/enqueue

Payload example:

{
  "notification_type": "email",
  "email": "testuser@example.com",
  "template_code": "WELCOME_TEMPLATE",
  "variables": { "name": "KC" },
  "priority": 1
}

## Test Email Sender (Direct enqueue to queue)

POST /enqueue-test-email
Creates a full payload, attaches UUID request ID, and sends to RabbitMQ (if available).
