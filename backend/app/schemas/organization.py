import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import MembershipRole


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Organization name")


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class MemberInvite(BaseModel):
    email: EmailStr
    role: MembershipRole = Field(default=MembershipRole.VIEWER)


class MemberUpdate(BaseModel):
    role: MembershipRole


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    role: MembershipRole
    created_at: datetime
