import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def log_audit_event(
    session: AsyncSession,
    organization_id: uuid.UUID,
    action: str,
    resource_type: str,
    user_id: Optional[uuid.UUID] = None,
    resource_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Creates an immutable security audit record for sensitive operations.
    """
    audit_entry = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        details=details or {}
    )
    session.add(audit_entry)
    await session.flush()
    return audit_entry
