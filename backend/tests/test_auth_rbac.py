import uuid
from datetime import timedelta
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.enums import MembershipRole
from app.models.organization import Membership, Organization
from app.models.user import User


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession):
    """Provides an AsyncClient bound to the FastAPI app with the test DB session override."""
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver/api/v1"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    """Test user registration and subsequent login."""
    # 1. Register
    reg_payload = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "New User"
    }
    response = await async_client.post("/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password_hash" not in data

    # 2. Login
    login_payload = {
        "email": "newuser@example.com",
        "password": "securepassword123"
    }
    login_resp = await async_client.post("/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials_fails(async_client: AsyncClient, tenant_setup: dict):
    """Test login with wrong password fails with HTTP 401."""
    payload = {
        "email": "user_a@org-a.com",
        "password": "wrongpassword"
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user_fails(async_client: AsyncClient, db_session: AsyncSession):
    """Test inactive user login fails."""
    pwd_hash = get_password_hash("password123")
    inactive_user = User(
        email="inactive@example.com",
        password_hash=pwd_hash,
        full_name="Inactive User",
        is_active=False
    )
    db_session.add(inactive_user)
    await db_session.commit()

    payload = {
        "email": "inactive@example.com",
        "password": "password123"
    }
    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_expired_credentials_fails(async_client: AsyncClient, tenant_setup: dict):
    """Test accessing protected route with expired access token fails."""
    user_a = tenant_setup["user_a"]
    # Issue token expired 1 hour ago
    expired_token = create_access_token(user_a.id, expires_delta=timedelta(hours=-1))

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower() or "could not validate" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unauthorized_organization_access_fails(async_client: AsyncClient, tenant_setup: dict):
    """Test user from Org A cannot access Org B details."""
    user_a = tenant_setup["user_a"]
    org_b = tenant_setup["org_b"]

    token_a = create_access_token(user_a.id)
    headers = {"Authorization": f"Bearer {token_a}"}

    # Attempt to fetch Org B details as User A
    response = await async_client.get(f"/organizations/{org_b.id}", headers=headers)
    assert response.status_code == 403
    assert "You do not have access to this organization" in response.json()["detail"]


@pytest.mark.asyncio
async def test_role_restrictions_viewer_cannot_invite_members(
    async_client: AsyncClient,
    db_session: AsyncSession,
    tenant_setup: dict
):
    """Test that VIEWER role is blocked from inviting members (requires OWNER or ADMIN)."""
    org_a = tenant_setup["org_a"]
    
    # Create a user with VIEWER role in Org A
    viewer_pwd = get_password_hash("password123")
    viewer_user = User(email="viewer@org-a.com", password_hash=viewer_pwd, full_name="Viewer User")
    db_session.add(viewer_user)
    await db_session.flush()

    viewer_mem = Membership(organization_id=org_a.id, user_id=viewer_user.id, role=MembershipRole.VIEWER)
    db_session.add(viewer_mem)
    await db_session.commit()

    token_viewer = create_access_token(viewer_user.id)
    headers = {"Authorization": f"Bearer {token_viewer}"}

    invite_payload = {"email": "someone@example.com", "role": "ANALYST"}
    response = await async_client.post(
        f"/organizations/{org_a.id}/members/invite",
        json=invite_payload,
        headers=headers
    )
    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_owner_can_invite_member_and_list_members(
    async_client: AsyncClient,
    db_session: AsyncSession,
    tenant_setup: dict
):
    """Test OWNER role can invite new member and view member list."""
    user_a = tenant_setup["user_a"]  # OWNER of org_a
    org_a = tenant_setup["org_a"]
    user_b = tenant_setup["user_b"]  # Existing user on system

    token_owner = create_access_token(user_a.id)
    headers = {"Authorization": f"Bearer {token_owner}"}

    # Invite user_b to org_a as ANALYST
    invite_payload = {"email": user_b.email, "role": "ANALYST"}
    invite_resp = await async_client.post(
        f"/organizations/{org_a.id}/members/invite",
        json=invite_payload,
        headers=headers
    )
    assert invite_resp.status_code == 201
    member_data = invite_resp.json()
    assert member_data["user_email"] == user_b.email
    assert member_data["role"] == "ANALYST"

    # List members
    list_resp = await async_client.get(f"/organizations/{org_a.id}/members", headers=headers)
    assert list_resp.status_code == 200
    members = list_resp.json()
    assert len(members) >= 2
