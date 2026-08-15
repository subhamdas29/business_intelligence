import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dataset import (
    Dataset,
    DatasetAnomaly,
    DatasetColumn,
    DatasetInsight,
    DatasetMetric,
    DatasetQualityReport,
)
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Repository managing Datasets and associated columns, quality reports, metrics, anomalies, and insights."""

    def __init__(self, session: AsyncSession):
        super().__init__(Dataset, session)

    async def get_by_table_name(self, organization_id: uuid.UUID, table_name: str) -> Optional[Dataset]:
        """Fetch dataset by unique internal table_name for an organization."""
        stmt = select(Dataset).where(
            Dataset.organization_id == organization_id,
            Dataset.table_name == table_name
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_columns(self, dataset_id: uuid.UUID, columns_data: List[dict]) -> List[DatasetColumn]:
        """Batch insert dataset columns."""
        cols = [DatasetColumn(dataset_id=dataset_id, **c) for c in columns_data]
        self.session.add_all(cols)
        await self.session.flush()
        return cols

    async def get_columns(self, organization_id: uuid.UUID, dataset_id: uuid.UUID) -> List[DatasetColumn]:
        """Get columns for a dataset, confirming tenant ownership."""
        dataset = await self.get_by_id(organization_id, dataset_id)
        if not dataset:
            return []
        
        stmt = select(DatasetColumn).where(DatasetColumn.dataset_id == dataset_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_quality_report(self, dataset_id: uuid.UUID, quality_score: float, duplicate_rows: int, missing_cells: int, issues: dict) -> DatasetQualityReport:
        """Attach dataset quality report."""
        report = DatasetQualityReport(
            dataset_id=dataset_id,
            quality_score=quality_score,
            duplicate_rows=duplicate_rows,
            missing_cells=missing_cells,
            issues=issues
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def add_metric(self, dataset_id: uuid.UUID, name: str, display_name: str, expression: str, description: Optional[str] = None) -> DatasetMetric:
        """Add semantic metric candidate."""
        metric = DatasetMetric(
            dataset_id=dataset_id,
            name=name,
            display_name=display_name,
            expression=expression,
            description=description
        )
        self.session.add(metric)
        await self.session.flush()
        return metric
