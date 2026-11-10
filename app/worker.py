
import json
import time
from datetime import datetime, timezone

import pika
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Registration
from app.messaging import (
    create_rabbitmq_connection,
    setup_queue
)


def process_registration(message: dict, db: Session):
    """Process one registration and update its database status."""

    request_id = message.get("request_id")

    registration = (
        db.query(Registration)
        .filter(Registration.request_id == request_id)
        .first()
    )

    if registration is None:
        print(f"Registration {request_id} not found. Skipping.")
        return

    registration.status = "PROCESSING"
    db.commit()

    print(f"Processing registration: {request_id}")

    # Simulate a time-consuming task
    time.sleep(2)

    registration.status = "COMPLETED"
    registration.completed_at = datetime.now(timezone.utc)

    db.commit()

    print(f"Completed registration: {request_id}")


def callback(channel, method, properties, body):
    """RabbitMQ message callback."""

    db = SessionLocal()

    try:
        message = json.loads(body.decode("utf-8"))

        process_registration(message, db)

        # Acknowledge only after successful database processing
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as error:
        db.rollback()

        print(f"Error processing message: {error}")

        # Requeue the message for another attempt
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )

    finally:
        db.close()


def start_worker():
    """Connect to RabbitMQ and continuously consume messages."""

    print("Starting QueueScale worker...")

    connection = create_rabbitmq_connection()
    channel = connection.channel()

    setup_queue(channel)

    # One unacknowledged message per worker at a time
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue="registration_queue",
        on_message_callback=callback
    )

    print("Worker is listening for registration messages...")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped.")
        channel.stop_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    start_worker()
