from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    file_path: str
    original_filename: str
    content_type: str

class Document(DocumentBase):
    id: int
    user_id: int
    file_path: str
    original_filename: str
    content_type: str
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    documents: List[Document]
    count: int