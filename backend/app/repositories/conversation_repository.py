import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import AnalysisRun, Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository managing Conversations, Messages, and AnalysisRuns."""

    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def add_message(
        self,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        sender: str,
        content: str
    ) -> Optional[Message]:
        """Add a message to a conversation after checking org ownership."""
        conv = await self.get_by_id(organization_id, conversation_id)
        if not conv:
            return None

        msg = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def create_analysis_run(
        self,
        organization_id: uuid.UUID,
        question: str,
        dataset_id: Optional[uuid.UUID] = None,
        message_id: Optional[uuid.UUID] = None,
        generated_plan: Optional[dict] = None,
        generated_sql: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        result_metadata: Optional[dict] = None,
        model: str = "gpt-4o",
        token_usage: Optional[dict] = None,
        status: str = "SUCCESS",
        error: Optional[str] = None
    ) -> AnalysisRun:
        """Log an AI analysis run with exact SQL and provenance."""
        run = AnalysisRun(
            organization_id=organization_id,
            message_id=message_id,
            dataset_id=dataset_id,
            question=question,
            generated_plan=generated_plan or {},
            generated_sql=generated_sql,
            execution_time_ms=execution_time_ms,
            result_metadata=result_metadata or {},
            model=model,
            token_usage=token_usage or {},
            status=status,
            error=error
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run
