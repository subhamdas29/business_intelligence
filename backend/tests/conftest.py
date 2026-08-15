import asyncio
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.models.base import Base
from app.models.enums import DatasetStatus, MembershipRole
from app.models.organization import Membership, Organization
from app.models.user import User
from app.models.dataset import Dataset
from app.models.dashboard import Dashboard
from app.models.conversation import Conversation

# Use SQLite in-memory engine for fast asynchronous unit testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def tenant_setup(db_session: AsyncSession):
    """Sets up two isolated organizations: Org A and Org B, each with users and datasets."""
    # 1. Users
    user_a = User(email="user_a@org-a.com", password_hash="hash_a", full_name="User A")
    user_b = User(email="user_b@org-b.com", password_hash="hash_b", full_name="User B")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # 2. Organizations
    org_a = Organization(name="Organization A", slug="org-a")
    org_b = Organization(name="Organization B", slug="org-b")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    # 3. Memberships
    mem_a = Membership(organization_id=org_a.id, user_id=user_a.id, role=MembershipRole.OWNER)
    mem_b = Membership(organization_id=org_b.id, user_id=user_b.id, role=MembershipRole.OWNER)
    db_session.add_all([mem_a, mem_b])
    await db_session.flush()

    # 4. Datasets
    dataset_a = Dataset(
        organization_id=org_a.id,
        created_by=user_a.id,
        name="Org A Confidential Data",
        source_type="csv",
        storage_path="path/a.csv",
        table_name="ds_org_a_table",
        status=DatasetStatus.READY,
        row_count=100
    )
    dataset_b = Dataset(
        organization_id=org_b.id,
        created_by=user_b.id,
        name="Org B Confidential Data",
        source_type="csv",
        storage_path="path/b.csv",
        table_name="ds_org_b_table",
        status=DatasetStatus.READY,
        row_count=200
    )
    db_session.add_all([dataset_a, dataset_b])
    await db_session.flush()

    # 5. Dashboards
    dashboard_a = Dashboard(organization_id=org_a.id, created_by=user_a.id, name="Org A Dashboard")
    dashboard_b = Dashboard(organization_id=org_b.id, created_by=user_b.id, name="Org B Dashboard")
    db_session.add_all([dashboard_a, dashboard_b])
    await db_session.flush()

    # 6. Conversations
    conv_a = Conversation(organization_id=org_a.id, user_id=user_a.id, title="Org A Discussion")
    conv_b = Conversation(organization_id=org_b.id, user_id=user_b.id, title="Org B Discussion")
    db_session.add_all([conv_a, conv_b])
    await db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "dataset_a": dataset_a,
        "dataset_b": dataset_b,
        "dashboard_a": dashboard_a,
        "dashboard_b": dashboard_b,
        "conv_a": conv_a,
        "conv_b": conv_b,
    }
