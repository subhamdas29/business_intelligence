import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import BigInteger, Boolean, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, JSONType, TimestampMixin, UUIDMixin
from app.models.enums import AnomalySeverity, DatasetStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Dataset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "datasets"

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
    source_type: Mapped[str] = mapped_column(String(50), default="csv", nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[DatasetStatus] = mapped_column(
        SQLEnum(DatasetStatus),
        default=DatasetStatus.UPLOADING,
        nullable=False,
        index=True
    )
    row_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="datasets")
    creator: Mapped[Optional["User"]] = relationship("User")
    versions: Mapped[List["DatasetVersion"]] = relationship(
        "DatasetVersion", back_populates="dataset", cascade="all, delete-orphan"
    )
    columns: Mapped[List["DatasetColumn"]] = relationship(
        "DatasetColumn", back_populates="dataset", cascade="all, delete-orphan"
    )
    quality_reports: Mapped[List["DatasetQualityReport"]] = relationship(
        "DatasetQualityReport", back_populates="dataset", cascade="all, delete-orphan"
    )
    metrics: Mapped[List["DatasetMetric"]] = relationship(
        "DatasetMetric", back_populates="dataset", cascade="all, delete-orphan"
    )
    anomalies: Mapped[List["DatasetAnomaly"]] = relationship(
        "DatasetAnomaly", back_populates="dataset", cascade="all, delete-orphan"
    )
    insights: Mapped[List["DatasetInsight"]] = relationship(
        "DatasetInsight", back_populates="dataset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} org_id={self.organization_id} name={self.name} status={self.status}>"


class DatasetVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    row_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Relationship
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="versions")


class DatasetColumn(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_columns"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inferred_type: Mapped[str] = mapped_column(String(50), nullable=False)
    semantic_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    nullable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unique_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cardinality: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    min_val: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_val: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mean_val: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    median_val: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sample_values: Mapped[List[Any]] = mapped_column(JSONType, default=list, nullable=False)

    # Relationship
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="columns")


class DatasetQualityReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_quality_reports"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    missing_cells: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    issues: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    # Relationship
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="quality_reports")


class DatasetMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_metrics"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    expression: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="metrics")


class DatasetAnomaly(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_anomalies"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[AnomalySeverity] = mapped_column(
        SQLEnum(AnomalySeverity),
        default=AnomalySeverity.MEDIUM,
        nullable=False
    )
    details: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    # Relationship
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="anomalies")


class DatasetInsight(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_insights"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    # Relationship
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="insights")
