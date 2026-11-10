
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Registration(Base):

    __tablename__ = "registrations"

    request_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    student_name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=False
    )

    event_name = Column(
        String(150),
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="QUEUED"
    )

    submitted_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )