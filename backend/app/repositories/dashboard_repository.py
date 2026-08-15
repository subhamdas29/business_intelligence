import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dashboard import Dashboard, DashboardWidget
from app.repositories.base import BaseRepository


class DashboardRepository(BaseRepository[Dashboard]):
    """Repository managing Dashboards and Widgets."""

    def __init__(self, session: AsyncSession):
        super().__init__(Dashboard, session)

    async def add_widget(
        self,
        organization_id: uuid.UUID,
        dashboard_id: uuid.UUID,
        title: str,
        visualization_type: str,
        dataset_id: Optional[uuid.UUID] = None,
        configuration: Optional[dict] = None,
        query: Optional[str] = None,
        position: Optional[dict] = None,
        dimensions: Optional[list] = None
    ) -> Optional[DashboardWidget]:
        """Add a widget to a dashboard after validating org ownership."""
        dashboard = await self.get_by_id(organization_id, dashboard_id)
        if not dashboard:
            return None

        widget = DashboardWidget(
            dashboard_id=dashboard_id,
            dataset_id=dataset_id,
            visualization_type=visualization_type,
            title=title,
            configuration=configuration or {},
            query=query,
            position=position or {},
            dimensions=dimensions or []
        )
        self.session.add(widget)
        await self.session.flush()
        await self.session.refresh(widget)
        return widget

    async def get_widgets(self, organization_id: uuid.UUID, dashboard_id: uuid.UUID) -> List[DashboardWidget]:
        """Get widgets for a dashboard, validating org ownership."""
        dashboard = await self.get_by_id(organization_id, dashboard_id)
        if not dashboard:
            return []

        stmt = select(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
