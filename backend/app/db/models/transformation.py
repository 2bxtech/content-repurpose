"""
SQLAlchemy model for transformations
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from enum import Enum

from app.core.models import BaseModel


class TransformationType(str, Enum):
    """Transformation type enumeration"""
    BLOG_POST = "BLOG_POST"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    EMAIL_SEQUENCE = "EMAIL_SEQUENCE"
    NEWSLETTER = "NEWSLETTER"
    SUMMARY = "SUMMARY"
    CUSTOM = "CUSTOM"


class TransformationStatus(str, Enum):
    """Transformation status enumeration"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transformation(BaseModel):
    """
    Transformation database model with multi-tenant support
    """
    __tablename__ = "transformations"

    # Multi-tenant references
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Transformation details
    transformation_type = Column(SQLEnum(TransformationType), nullable=False)
    parameters = Column(JSONB, nullable=True)
    status = Column(SQLEnum(TransformationStatus), nullable=False, default=TransformationStatus.PENDING)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # AI provider tracking (Phase 7)
    ai_provider = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)

    # Background task tracking (Phase 4)
    task_id = Column(String(255), nullable=True)
    ai_model = Column(String(100), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="transformations")
    user = relationship("User", back_populates="transformations")
    document = relationship("Document", back_populates="transformations")

    def __repr__(self):
        return f"<Transformation(id={self.id}, type={self.transformation_type}, status={self.status})>"
