from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, func, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Base model with audit trail and soft delete"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Audit trail
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

class WorkspaceMixin:
    """Mixin for models that belong to a workspace (RLS support)"""
    
    @classmethod
    def create_workspace_index(cls, table_name: str):
        return Index(
            f"idx_{table_name}_workspace_active",
            "workspace_id",
            postgresql_where=Column("deleted_at").is_(None)
        )