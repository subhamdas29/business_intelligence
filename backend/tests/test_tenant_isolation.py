import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.conversation_repository import ConversationRepository


@pytest.mark.asyncio
async def test_org_a_cannot_get_org_b_dataset_by_id(db_session: AsyncSession, tenant_setup: dict):
    """Test that Organization A cannot fetch Organization B's dataset even with a known dataset ID."""
    org_a = tenant_setup["org_a"]
    dataset_b = tenant_setup["dataset_b"]

    repo = DatasetRepository(db_session)
    result = await repo.get_by_id(organization_id=org_a.id, entity_id=dataset_b.id)

    assert result is None, "Security Violation: Org A was able to access Org B's dataset by ID!"


@pytest.mark.asyncio
async def test_org_a_cannot_list_org_b_datasets(db_session: AsyncSession, tenant_setup: dict):
    """Test that listing datasets for Organization A returns ONLY Org A datasets."""
    org_a = tenant_setup["org_a"]
    dataset_a = tenant_setup["dataset_a"]

    repo = DatasetRepository(db_session)
    datasets = await repo.list(organization_id=org_a.id)

    assert len(datasets) == 1
    assert datasets[0].id == dataset_a.id
    assert all(ds.organization_id == org_a.id for ds in datasets)


@pytest.mark.asyncio
async def test_org_a_cannot_update_org_b_dataset(db_session: AsyncSession, tenant_setup: dict):
    """Test that Organization A cannot update Organization B's dataset."""
    org_a = tenant_setup["org_a"]
    dataset_b = tenant_setup["dataset_b"]

    repo = DatasetRepository(db_session)
    updated = await repo.update(
        organization_id=org_a.id,
        entity_id=dataset_b.id,
        name="Hacked Name by Org A"
    )

    assert updated is None, "Security Violation: Org A was able to update Org B's dataset!"

    # Verify Org B's dataset name was unchanged
    org_b = tenant_setup["org_b"]
    original_b = await repo.get_by_id(organization_id=org_b.id, entity_id=dataset_b.id)
    assert original_b is not None
    assert original_b.name == "Org B Confidential Data"


@pytest.mark.asyncio
async def test_org_a_cannot_delete_org_b_dataset(db_session: AsyncSession, tenant_setup: dict):
    """Test that Organization A cannot delete Organization B's dataset."""
    org_a = tenant_setup["org_a"]
    dataset_b = tenant_setup["dataset_b"]

    repo = DatasetRepository(db_session)
    deleted = await repo.delete(organization_id=org_a.id, entity_id=dataset_b.id)

    assert deleted is False, "Security Violation: Org A was able to delete Org B's dataset!"

    # Verify Org B's dataset still exists
    org_b = tenant_setup["org_b"]
    still_exists = await repo.get_by_id(organization_id=org_b.id, entity_id=dataset_b.id)
    assert still_exists is not None


@pytest.mark.asyncio
async def test_org_a_cannot_access_org_b_dashboards(db_session: AsyncSession, tenant_setup: dict):
    """Test tenant isolation on dashboards."""
    org_a = tenant_setup["org_a"]
    dashboard_b = tenant_setup["dashboard_b"]

    dash_repo = DashboardRepository(db_session)
    result = await dash_repo.get_by_id(organization_id=org_a.id, entity_id=dashboard_b.id)

    assert result is None


@pytest.mark.asyncio
async def test_org_a_cannot_access_org_b_conversations(db_session: AsyncSession, tenant_setup: dict):
    """Test tenant isolation on AI analyst conversations."""
    org_a = tenant_setup["org_a"]
    conv_b = tenant_setup["conv_b"]

    conv_repo = ConversationRepository(db_session)
    result = await conv_repo.get_by_id(organization_id=org_a.id, entity_id=conv_b.id)

    assert result is None
