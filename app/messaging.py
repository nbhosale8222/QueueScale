
import json
import os
import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5673"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "queuescale")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "queuescale_dev")

EXCHANGE_NAME = "queuescale_exchange"
QUEUE_NAME = "registration_queue"
ROUTING_KEY = "registration.created"


def create_rabbitmq_connection():
    """Create and return a connection to RabbitMQ."""

    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30
    )

    return pika.BlockingConnection(parameters)


def setup_queue(channel):
    """Declare the durable exchange and registration queue."""

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="direct",
        durable=True
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )


def publish_registration(message: dict):
    """Publish a registration message to RabbitMQ."""

    connection = create_rabbitmq_connection()

    try:
        channel = connection.channel()

        setup_queue(channel)

        channel.confirm_delivery()

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json"
            ),
            mandatory=True
        )

        return True

    finally:
        if connection.is_open:
            connection.close()
