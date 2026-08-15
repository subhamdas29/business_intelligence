import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, JSONType, TimestampMixin, UUIDMixin
from app.models.enums import VisualizationType

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.organization import Organization
    from app.models.user import User


class Dashboard(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dashboards"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="dashboards")
    creator: Mapped[Optional["User"]] = relationship("User")
    widgets: Mapped[List["DashboardWidget"]] = relationship(
        "DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} org_id={self.organization_id} name={self.name}>"


class DashboardWidget(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dashboard_widgets"

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    visualization_type: Mapped[VisualizationType] = mapped_column(
        SQLEnum(VisualizationType),
        default=VisualizationType.BAR_CHART,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    dimensions: Mapped[List[Any]] = mapped_column(JSONType, default=list, nullable=False)

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset")
