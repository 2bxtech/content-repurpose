from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

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

class TransformationBase(BaseModel):
    document_id: uuid.UUID
    transformation_type: TransformationType
    parameters: Optional[Dict[str, Any]] = {}

class TransformationCreate(TransformationBase):
    pass

class Transformation(TransformationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: TransformationStatus = TransformationStatus.PENDING
    result: Optional[str] = None
    task_id: Optional[str] = None  # Celery task ID for tracking
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TransformationList(BaseModel):
    transformations: List[Transformation]
    count: int