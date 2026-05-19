import uuid

from sqlalchemy import Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Result(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
    )
    serialized_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    embedding: Mapped[list] = mapped_column(
        ARRAY(Float),
        nullable=False,
    )
    cluster: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    x: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    y: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )