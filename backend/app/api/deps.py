import uuid
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.security import decode_token
from app.models.dataset import Dataset
from app.models.enums import MembershipRole
from app.models.organization import Membership
from app.models.user import User

security_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extracts and verifies JWT bearer access token, returning authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensures current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return current_user


async def require_authenticated_user(
    user: User = Depends(get_current_active_user)
) -> User:
    """Reusable dependency guaranteeing an authenticated active user."""
    return user


async def require_organization_member(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Membership:
    """Verifies user belongs to the requested organization."""
    stmt = select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == current_user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )
    return membership


def require_role(allowed_roles: List[MembershipRole]) -> Callable:
    """Factory dependency requiring user to possess one of allowed_roles in the organization."""
    async def role_checker(
        organization_id: uuid.UUID,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> Membership:
        membership = await require_organization_member(organization_id, current_user, db)
        
        # Check role permission
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {[r.value for r in allowed_roles]}, your role: {membership.role.value}"
            )
        return membership
        
    return role_checker


def require_dataset_access(allowed_roles: Optional[List[MembershipRole]] = None) -> Callable:
    """Factory dependency verifying dataset exists, belongs to tenant, and user is authorized."""
    async def dataset_checker(
        organization_id: uuid.UUID,
        dataset_id: uuid.UUID,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> Dataset:
        # First verify organization membership & optional role constraint
        membership = await require_organization_member(organization_id, current_user, db)
        if allowed_roles and membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied to access dataset"
            )
            
        stmt = select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.organization_id == organization_id
        )
        result = await db.execute(stmt)
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or does not belong to this organization"
            )
        return dataset

    return dataset_checker
