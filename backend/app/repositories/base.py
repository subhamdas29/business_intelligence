import uuid
from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository enforcing compulsory multi-tenant isolation.
    Every read, write, update, and delete method mandates an organization_id parameter.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, organization_id: uuid.UUID, entity_id: uuid.UUID) -> Optional[ModelType]:
        """Fetch entity by ID, strictly filtered by organization_id."""
        stmt = select(self.model).where(
            self.model.id == entity_id,
            self.model.organization_id == organization_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """List entities for a tenant with pagination."""
        stmt = select(self.model).where(
            self.model.organization_id == organization_id
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, organization_id: uuid.UUID) -> int:
        """Count total entities for a tenant."""
        stmt = select(self.model).where(self.model.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def create(self, organization_id: uuid.UUID, **kwargs: Any) -> ModelType:
        """Create a new entity with organization_id bound."""
        kwargs["organization_id"] = organization_id
        db_obj = self.model(**kwargs)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        organization_id: uuid.UUID,
        entity_id: uuid.UUID,
        **kwargs: Any
    ) -> Optional[ModelType]:
        """Update entity by ID, confirming tenant ownership."""
        db_obj = await self.get_by_id(organization_id, entity_id)
        if not db_obj:
            return None
        
        for key, value in kwargs.items():
            if hasattr(db_obj, key) and key not in ("id", "organization_id"):
                setattr(db_obj, key, value)
                
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, organization_id: uuid.UUID, entity_id: uuid.UUID) -> bool:
        """Delete entity by ID, confirming tenant ownership."""
        db_obj = await self.get_by_id(organization_id, entity_id)
        if not db_obj:
            return False
        
        await self.session.delete(db_obj)
        await self.session.flush()
        return True
