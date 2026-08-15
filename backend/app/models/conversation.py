import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, JSONType, TimestampMixin, UUIDMixin
from app.models.enums import AnalysisRunStatus

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.organization import Organization
    from app.models.user import User


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="conversations")
    user: Mapped[Optional["User"]] = relationship("User")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} org_id={self.organization_id} title={self.title}>"


class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sender: Mapped[str] = mapped_column(String(50), nullable=False)  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    analysis_run: Mapped[Optional["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="message", uselist=False, cascade="all, delete-orphan"
    )


class AnalysisRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_runs"

    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_plan: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o", nullable=False)
    token_usage: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[AnalysisRunStatus] = mapped_column(
        SQLEnum(AnalysisRunStatus),
        default=AnalysisRunStatus.SUCCESS,
        nullable=False,
        index=True
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="analysis_run")
    organization: Mapped["Organization"] = relationship("Organization")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset")
