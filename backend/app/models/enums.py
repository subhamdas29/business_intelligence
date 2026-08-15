from enum import Enum


class MembershipRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class DatasetStatus(str, Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisRunStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VisualizationType(str, Enum):
    LINE_CHART = "LINE_CHART"
    BAR_CHART = "BAR_CHART"
    SCATTER_PLOT = "SCATTER_PLOT"
    PIE_CHART = "PIE_CHART"
    HISTOGRAM = "HISTOGRAM"
    KPI_CARD = "KPI_CARD"
    TABLE = "TABLE"
    MAP = "MAP"


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
