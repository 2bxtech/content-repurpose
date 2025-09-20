# backend/app/db/models/transformation.py
from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.models import BaseModel
from enum import Enum

class TransformationStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING" 
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TransformationType(str, Enum):
    BLOG_POST = "BLOG_POST"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    EMAIL_SEQUENCE = "EMAIL_SEQUENCE"
    NEWSLETTER = "NEWSLETTER"
    SUMMARY = "SUMMARY"
    CUSTOM = "CUSTOM"

class Transformation(BaseModel):
    __tablename__ = "transformations"
    
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    transformation_type = Column(SQLEnum(TransformationType), nullable=False)
    parameters = Column(JSONB, default={})
    status = Column(SQLEnum(TransformationStatus), default=TransformationStatus.PENDING)
    result = Column(Text)
    error_message = Column(Text)
    task_id = Column(String(255))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="transformations")
    user = relationship("User", back_populates="transformations")
    document = relationship("Document", back_populates="transformations")