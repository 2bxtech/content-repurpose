import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List, Annotated, Optional
from datetime import datetime

from app.models.documents import Document, DocumentCreate, DocumentList, DocumentStatus
from app.api.routes.auth import get_current_user
from app.core.config import settings

# Mock database for documents - in a real app, use a proper database
DOCUMENTS_DB = []
document_id_counter = 1

router = APIRouter()

def validate_file_extension(filename: str) -> bool:
    ext = filename.split(".")[-1].lower()
    return ext in settings.ALLOWED_EXTENSIONS

@router.post("/documents/upload", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    global document_id_counter
    
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset file pointer to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024 * 1024)}MB"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{current_user['id']}_{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Create document record
    document = {
        "id": document_id_counter,
        "user_id": current_user["id"],
        "title": title,
        "description": description,
        "file_path": file_path,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "status": DocumentStatus.PENDING,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    DOCUMENTS_DB.append(document)
    document_id_counter += 1
    
    return document

@router.get("/documents", response_model=DocumentList)
async def get_user_documents(current_user: dict = Depends(get_current_user)):
    user_documents = [doc for doc in DOCUMENTS_DB if doc["user_id"] == current_user["id"]]
    return {"documents": user_documents, "count": len(user_documents)}

@router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: int, current_user: dict = Depends(get_current_user)):
    for doc in DOCUMENTS_DB:
        if doc["id"] == document_id and doc["user_id"] == current_user["id"]:
            return doc
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found"
    )

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, current_user: dict = Depends(get_current_user)):
    for i, doc in enumerate(DOCUMENTS_DB):
        if doc["id"] == document_id and doc["user_id"] == current_user["id"]:
            # Delete the file
            if os.path.exists(doc["file_path"]):
                os.remove(doc["file_path"])
            
            # Remove document from db
            DOCUMENTS_DB.pop(i)
            return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Document not found"
    )