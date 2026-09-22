"""SQLAlchemy 2.0 database models and connection session factory.

Provides relational schema definitions for pipeline execution audits and extracted records.
"""

from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

from src.config import settings
from src.utils.logger import logger


class Base(DeclarativeBase):
    """Declarative base class for all enterprise database models."""

    pass


class PipelineRunRecord(Base):
    """Tracks audit logs and execution metrics for each LangGraph pipeline run."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    run_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class ExtractedDocumentRecord(Base):
    """Stores persisted documents and payloads extracted from target web sources."""

    __tablename__ = "extracted_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=True)
    raw_content: Mapped[str] = mapped_column(Text, nullable=True)
    parsed_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


# Database Engine and Session Factory configuration
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    """Provides a transactional database session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("Database session rolled back due to error: {}", exc)
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initializes tables within the configured PostgreSQL schema."""
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables successfully initialized.")
