from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.models import BaseModel, WorkspaceMixin
from enum import Enum

class TransformationType(str, Enum):
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL_SEQUENCE = "email_sequence"
    NEWSLETTER = "newsletter"
    SUMMARY = "summary"
    CUSTOM = "custom"

class TransformationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transformation(BaseModel, WorkspaceMixin):
    """Enhanced Transformation model"""
    __tablename__ = "transformations"
    
    # Multi-tenant support (RLS ready)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Transformation details
    transformation_type = Column(SQLEnum(TransformationType), nullable=False)
    parameters = Column(JSONB, default={})
    
    # Status and results
    status = Column(SQLEnum(TransformationStatus), default=TransformationStatus.PENDING)
    result = Column(Text)
    error_message = Column(Text)
    task_id = Column(String(255))  # Celery task ID for tracking
    
    # AI processing metadata
    ai_provider = Column(String(50))
    ai_model = Column(String(100))  # AI model used
    tokens_used = Column(Integer)
    processing_time_seconds = Column(Integer)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="transformations")
    user = relationship("User", back_populates="transformations")
    document = relationship("Document", back_populates="transformations")
    
    # Performance indexes
    __table_args__ = (
        Index("idx_transformations_workspace_user", "workspace_id", "user_id"),
        Index("idx_transformations_document", "document_id"),
        Index("idx_transformations_status_created", "status", "created_at"),
        WorkspaceMixin.create_workspace_index("transformations"),
    )