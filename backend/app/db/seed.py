import asyncio
import logging
import uuid
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import AsyncSessionLocal
from app.models.enums import (
    AnalysisRunStatus,
    AnomalySeverity,
    DatasetStatus,
    MembershipRole,
    VisualizationType,
)
from app.models.organization import Membership, Organization
from app.models.user import User
from app.models.dataset import (
    Dataset,
    DatasetColumn,
    DatasetMetric,
    DatasetQualityReport,
)
from app.models.dashboard import Dashboard, DashboardWidget
from app.models.conversation import AnalysisRun, Conversation, Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

from app.core.security import get_password_hash


async def seed_database():
    logger.info("Starting database seeding...")
    async with AsyncSessionLocal() as session:
        # 1. Create Users
        alice = User(
            email="alice@acme.com",
            password_hash=get_password_hash("password123"),
            full_name="Alice Vance",
            is_active=True,
            is_superuser=True
        )
        bob = User(
            email="bob@stark.com",
            password_hash=get_password_hash("password123"),
            full_name="Bob Stark",
            is_active=True,
            is_superuser=False
        )
        session.add_all([alice, bob])
        await session.flush()

        # 2. Create Organizations
        acme_org = Organization(name="Acme Corp", slug="acme-corp")
        stark_org = Organization(name="Stark Industries", slug="stark-industries")
        session.add_all([acme_org, stark_org])
        await session.flush()

        # 3. Create Memberships
        mem_alice = Membership(
            organization_id=acme_org.id,
            user_id=alice.id,
            role=MembershipRole.OWNER
        )
        mem_bob = Membership(
            organization_id=stark_org.id,
            user_id=bob.id,
            role=MembershipRole.OWNER
        )
        session.add_all([mem_alice, mem_bob])
        await session.flush()

        # 4. Create Dataset for Acme Corp
        acme_dataset = Dataset(
            organization_id=acme_org.id,
            created_by=alice.id,
            name="Q2 Sales Report 2026",
            description="Acme quarterly revenue and profit breakdown by region",
            source_type="csv",
            storage_path="uploads/acme/q2_sales_2026.csv",
            table_name="ds_acme_q2_sales",
            status=DatasetStatus.READY,
            row_count=1000,
            column_count=5
        )
        
        # Dataset for Stark Industries (Tenant Isolation testing seed)
        stark_dataset = Dataset(
            organization_id=stark_org.id,
            created_by=bob.id,
            name="Stark Weapons R&D Expenses",
            description="Confidential Stark Industries research expenses",
            source_type="csv",
            storage_path="uploads/stark/rd_expenses.csv",
            table_name="ds_stark_rd_expenses",
            status=DatasetStatus.READY,
            row_count=500,
            column_count=4
        )
        session.add_all([acme_dataset, stark_dataset])
        await session.flush()

        # 5. Add Columns for Acme Dataset
        cols = [
            DatasetColumn(
                dataset_id=acme_dataset.id,
                column_name="Transaction Date",
                normalized_name="transaction_date",
                inferred_type="TIMESTAMP",
                semantic_type="date",
                nullable=False
            ),
            DatasetColumn(
                dataset_id=acme_dataset.id,
                column_name="Region",
                normalized_name="region",
                inferred_type="VARCHAR",
                semantic_type="dimension",
                nullable=False,
                cardinality=4,
                sample_values=["North", "South", "East", "West"]
            ),
            DatasetColumn(
                dataset_id=acme_dataset.id,
                column_name="Revenue ($)",
                normalized_name="revenue",
                inferred_type="FLOAT",
                semantic_type="metric",
                nullable=False,
                min_val="100.0",
                max_val="50000.0",
                mean_val=15250.75,
                median_val=12000.0
            ),
            DatasetColumn(
                dataset_id=acme_dataset.id,
                column_name="Profit ($)",
                normalized_name="profit",
                inferred_type="FLOAT",
                semantic_type="metric",
                nullable=False,
                min_val="20.0",
                max_val="15000.0",
                mean_val=4500.50,
                median_val=3800.0
            )
        ]
        session.add_all(cols)

        # 6. Add Quality Report & Metrics for Acme
        qr = DatasetQualityReport(
            dataset_id=acme_dataset.id,
            quality_score=98.5,
            duplicate_rows=0,
            missing_cells=2,
            issues={"warnings": ["2 missing cells filled with zero"]}
        )
        metric_rev = DatasetMetric(
            dataset_id=acme_dataset.id,
            name="total_revenue",
            display_name="Total Revenue",
            expression="SUM(revenue)",
            description="Sum of revenue across all regions"
        )
        session.add_all([qr, metric_rev])

        # 7. Create Dashboard & Widgets for Acme
        dashboard = Dashboard(
            organization_id=acme_org.id,
            created_by=alice.id,
            name="Executive Sales Dashboard",
            description="Overview of sales performance in Q2"
        )
        session.add(dashboard)
        await session.flush()

        widget = DashboardWidget(
            dashboard_id=dashboard.id,
            dataset_id=acme_dataset.id,
            visualization_type=VisualizationType.BAR_CHART,
            title="Revenue by Region",
            description="Total sales broken down by geographic sales region",
            query="SELECT region, SUM(revenue) AS total_revenue FROM ds_acme_q2_sales GROUP BY region;",
            configuration={"xAxis": "region", "yAxis": "total_revenue"},
            dimensions=["region"]
        )
        session.add(widget)

        # 8. Create Conversation & AnalysisRun for Acme
        conv = Conversation(
            organization_id=acme_org.id,
            user_id=alice.id,
            title="Q2 Revenue Breakdown Inquiry"
        )
        session.add(conv)
        await session.flush()

        msg = Message(
            conversation_id=conv.id,
            sender="user",
            content="Which region generated the highest profit in Q2?"
        )
        session.add(msg)
        await session.flush()

        analysis_run = AnalysisRun(
            message_id=msg.id,
            organization_id=acme_org.id,
            dataset_id=acme_dataset.id,
            question="Which region generated the highest profit in Q2?",
            generated_plan={
                "metrics": [{"column": "profit", "aggregation": "SUM"}],
                "dimensions": ["region"],
                "sort_by": [{"column": "profit", "direction": "DESC"}]
            },
            generated_sql="SELECT region, SUM(profit) AS total_profit FROM ds_acme_q2_sales GROUP BY region ORDER BY total_profit DESC LIMIT 1;",
            execution_time_ms=14.2,
            result_metadata={"rows_returned": 1, "top_region": "North", "profit": 185000.0},
            model="gpt-4o",
            status=AnalysisRunStatus.SUCCESS
        )
        session.add(analysis_run)

        await session.commit()
        logger.info("Successfully seeded database!")


if __name__ == "__main__":
    asyncio.run(seed_database())
