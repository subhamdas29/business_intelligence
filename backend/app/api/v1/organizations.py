import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    require_organization_member,
    require_role,
)
from app.core.audit import log_audit_event
from app.core.db import get_db
from app.models.enums import MembershipRole
from app.models.organization import Membership, Organization
from app.models.user import User
from app.schemas.organization import (
    MemberInvite,
    MemberResponse,
    MemberUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["Organizations & Memberships"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization. The creator is automatically assigned the OWNER role.
    """
    # Slugify organization name
    slug = org_in.name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]

    new_org = Organization(
        name=org_in.name,
        slug=slug
    )
    db.add(new_org)
    await db.flush()

    # Create OWNER membership for creator
    owner_membership = Membership(
        organization_id=new_org.id,
        user_id=current_user.id,
        role=MembershipRole.OWNER
    )
    db.add(owner_membership)

    await log_audit_event(
        db,
        organization_id=new_org.id,
        user_id=current_user.id,
        action="organization.created",
        resource_type="organization",
        resource_id=new_org.id,
        ip_address=request.client.host if request.client else None
    )

    await db.commit()
    await db.refresh(new_org)
    return new_org


@router.get("", response_model=List[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all organizations the authenticated user belongs to.
    """
    stmt = (
        select(Organization)
        .join(Membership, Organization.id == Membership.organization_id)
        .where(Membership.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: uuid.UUID,
    membership: Membership = Depends(require_organization_member),
    db: AsyncSession = Depends(get_db)
):
    """
    Get organization details. Requires membership.
    """
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: uuid.UUID,
    org_update: OrganizationUpdate,
    request: Request,
    membership: Membership = Depends(require_role([MembershipRole.OWNER, MembershipRole.ADMIN])),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update organization name. Requires OWNER or ADMIN role.
    """
    stmt = select(Organization).where(Organization.id == organization_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org_update.name:
        org.name = org_update.name

    await log_audit_event(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
        action="organization.updated",
        resource_type="organization",
        resource_id=organization_id,
        ip_address=request.client.host if request.client else None
    )

    await db.commit()
    await db.refresh(org)
    return org


# ==========================================
# MEMBERSHIP ENDPOINTS
# ==========================================

@router.post("/{organization_id}/members/invite", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    organization_id: uuid.UUID,
    invite_in: MemberInvite,
    request: Request,
    membership: Membership = Depends(require_role([MembershipRole.OWNER, MembershipRole.ADMIN])),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invite a user to the organization by email. Requires OWNER or ADMIN role.
    """
    # Find invited user by email
    stmt = select(User).where(User.email == invite_in.email)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {invite_in.email} is not registered on the platform"
        )

    # Check if already a member
    mem_stmt = select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == target_user.id
    )
    mem_result = await db.execute(mem_stmt)
    existing_member = mem_result.scalar_one_or_none()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )

    new_membership = Membership(
        organization_id=organization_id,
        user_id=target_user.id,
        role=invite_in.role
    )
    db.add(new_membership)

    await log_audit_event(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
        action="member.invited",
        resource_type="membership",
        resource_id=new_membership.id,
        ip_address=request.client.host if request.client else None,
        details={"invited_user_email": target_user.email, "role": invite_in.role.value}
    )

    await db.commit()
    await db.refresh(new_membership)

    return MemberResponse(
        id=new_membership.id,
        organization_id=new_membership.organization_id,
        user_id=target_user.id,
        user_email=target_user.email,
        user_full_name=target_user.full_name,
        role=new_membership.role,
        created_at=new_membership.created_at
    )


@router.get("/{organization_id}/members", response_model=List[MemberResponse])
async def list_members(
    organization_id: uuid.UUID,
    membership: Membership = Depends(require_organization_member),
    db: AsyncSession = Depends(get_db)
):
    """
    List all members of an organization. Requires any valid membership.
    """
    stmt = (
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(Membership.organization_id == organization_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        MemberResponse(
            id=mem.id,
            organization_id=mem.organization_id,
            user_id=usr.id,
            user_email=usr.email,
            user_full_name=usr.full_name,
            role=mem.role,
            created_at=mem.created_at
        )
        for mem, usr in rows
    ]


@router.patch("/{organization_id}/members/{member_id}", response_model=MemberResponse)
async def update_member_role(
    organization_id: uuid.UUID,
    member_id: uuid.UUID,
    member_update: MemberUpdate,
    request: Request,
    membership: Membership = Depends(require_role([MembershipRole.OWNER, MembershipRole.ADMIN])),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update member role. Requires OWNER or ADMIN role.
    """
    stmt = (
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(
            Membership.id == member_id,
            Membership.organization_id == organization_id
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization"
        )

    target_mem, target_usr = row
    target_mem.role = member_update.role

    await log_audit_event(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
        action="member.role_updated",
        resource_type="membership",
        resource_id=target_mem.id,
        ip_address=request.client.host if request.client else None,
        details={"new_role": member_update.role.value}
    )

    await db.commit()
    await db.refresh(target_mem)

    return MemberResponse(
        id=target_mem.id,
        organization_id=target_mem.organization_id,
        user_id=target_usr.id,
        user_email=target_usr.email,
        user_full_name=target_usr.full_name,
        role=target_mem.role,
        created_at=target_mem.created_at
    )


@router.delete("/{organization_id}/members/{member_id}", status_code=status.HTTP_200_OK)
async def remove_member(
    organization_id: uuid.UUID,
    member_id: uuid.UUID,
    request: Request,
    membership: Membership = Depends(require_role([MembershipRole.OWNER, MembershipRole.ADMIN])),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from the organization. Requires OWNER or ADMIN role.
    """
    stmt = select(Membership).where(
        Membership.id == member_id,
        Membership.organization_id == organization_id
    )
    result = await db.execute(stmt)
    target_mem = result.scalar_one_or_none()

    if not target_mem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization"
        )

    await db.delete(target_mem)

    await log_audit_event(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
        action="member.removed",
        resource_type="membership",
        resource_id=member_id,
        ip_address=request.client.host if request.client else None
    )

    await db.commit()
    return {"message": "Member successfully removed from organization"}
