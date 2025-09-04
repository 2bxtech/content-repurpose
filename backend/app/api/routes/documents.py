import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime
import uuid

from app.models.documents import Document, DocumentList, DocumentStatus
from app.db.models.document import Document as DocumentDB
from app.api.routes.auth import get_current_active_user
from app.api.routes.workspaces import get_current_workspace_context
from app.core.database import get_db_session
from app.core.config import settings
from app.services.workspace_service import workspace_service
from app.services.file_processor import file_processor  # Enhanced file processor

# Mock database for documents - will be replaced when DB is connected
DOCUMENTS_DB = []
document_id_counter = 1

router = APIRouter()


def validate_file_extension(filename: str) -> bool:
    """Enhanced file extension validation"""
    return file_processor.validate_file_type(
        "application/octet-stream", filename
    )  # Basic check


@router.post(
    "/documents/upload", response_model=Document, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    global document_id_counter

    # Enhanced file validation using new file processor
    if not file_processor.validate_file_type(file.content_type, file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. File: {file.filename}, MIME: {file.content_type}",
        )

    # Read file content for processing
    content = await file.read()
    await file.seek(0)  # Reset file pointer to beginning

    # Validate file size
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Size: {file_size / (1024 * 1024):.1f}MB, Maximum: {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.1f}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file not allowed"
        )

    workspace_id = workspace_context["workspace_id"]

    # Check workspace limits (if using database)
    if db:
        can_create, error_msg = await workspace_service.check_workspace_limits(
            db, workspace_id, "create_document"
        )
        if not can_create:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )

        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{current_user['id']}_{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    try:
        # Enhanced file processing with security validation and content extraction
        processing_result = await file_processor.process_file(
            file_path=file_path,
            content_type=file.content_type,
            original_filename=file.filename,
        )

        if not processing_result.security_scan_passed:
            # Clean up file if security scan failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File failed security validation",
            )

    except ValueError as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File processing failed: {str(e)}",
        )
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file processing: {str(e)}",
        )

    if db:
        try:
            # Create document record in database with enhanced metadata
            document_db = DocumentDB(
                workspace_id=workspace_id,
                user_id=current_user["id"],
                title=title,
                description=description,
                file_path=file_path,
                original_filename=file.filename,
                content_type=file.content_type,
                file_size=file_size,
                # Enhanced Phase 6 fields
                extracted_text=processing_result.content,
                doc_metadata={
                    **processing_result.metadata,
                    "file_hash": processing_result.file_hash,
                    "preview_path": processing_result.preview_path,
                    "content_encoding": processing_result.content_encoding,
                    "word_count": processing_result.word_count,
                    "extraction_method": processing_result.extraction_method,
                },
                status=DocumentStatus.COMPLETED,  # Mark as completed since processing succeeded
                created_by=current_user["id"],
            )

            db.add(document_db)
            await db.commit()
            await db.refresh(document_db)

            return Document(
                id=document_db.id,
                user_id=document_db.user_id,
                title=document_db.title,
                description=document_db.description,
                file_path=document_db.file_path,
                original_filename=document_db.original_filename,
                content_type=document_db.content_type,
                status=document_db.status,
                created_at=document_db.created_at,
                updated_at=document_db.updated_at,
            )

        except Exception as e:
            # Clean up file if database operation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document record: {str(e)}",
            )
        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # Fallback to in-memory storage
        document = {
            "id": document_id_counter,
            "user_id": current_user["id"],
            "title": title,
            "description": description,
            "file_path": file_path,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "status": DocumentStatus.COMPLETED,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            # Enhanced metadata from processing
            "extracted_text": processing_result.content,
            "metadata": processing_result.metadata,
            "file_hash": processing_result.file_hash,
            "preview_path": processing_result.preview_path,
        }

        DOCUMENTS_DB.append(document)
        document_id_counter += 1

        return document


@router.get("/documents", response_model=DocumentList)
async def get_user_documents(
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            # Get documents with RLS automatically filtering by workspace
            stmt = (
                select(DocumentDB)
                .where(
                    and_(
                        DocumentDB.workspace_id == workspace_id,
                        DocumentDB.user_id == current_user["id"],
                        DocumentDB.deleted_at.is_(None),
                    )
                )
                .order_by(DocumentDB.created_at.desc())
            )

            result = await db.execute(stmt)
            documents_db = result.scalars().all()

            documents = []
            for doc_db in documents_db:
                documents.append(
                    Document(
                        id=doc_db.id,
                        user_id=doc_db.user_id,
                        title=doc_db.title,
                        description=doc_db.description,
                        file_path=doc_db.file_path,
                        original_filename=doc_db.original_filename,
                        content_type=doc_db.content_type,
                        status=doc_db.status,
                        created_at=doc_db.created_at,
                        updated_at=doc_db.updated_at,
                    )
                )

            return DocumentList(documents=documents, count=len(documents))

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # Fallback to in-memory storage
        user_documents = [
            doc for doc in DOCUMENTS_DB if doc["user_id"] == current_user["id"]
        ]
        return DocumentList(documents=user_documents, count=len(user_documents))


@router.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(DocumentDB).where(
                and_(
                    DocumentDB.id == document_id,
                    DocumentDB.workspace_id == workspace_id,
                    DocumentDB.user_id == current_user["id"],
                    DocumentDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            document_db = result.scalar_one_or_none()

            if not document_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            return Document(
                id=document_db.id,
                user_id=document_db.user_id,
                title=document_db.title,
                description=document_db.description,
                file_path=document_db.file_path,
                original_filename=document_db.original_filename,
                content_type=document_db.content_type,
                status=document_db.status,
                created_at=document_db.created_at,
                updated_at=document_db.updated_at,
            )

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # Fallback to in-memory storage - convert UUID to int for compatibility
        try:
            doc_id = int(str(document_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        for doc in DOCUMENTS_DB:
            if doc["id"] == doc_id and doc["user_id"] == current_user["id"]:
                return doc

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )


@router.get("/documents/{document_id}/preview")
async def get_document_preview(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get document preview image"""
    from fastapi.responses import FileResponse

    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(DocumentDB).where(
                and_(
                    DocumentDB.id == document_id,
                    DocumentDB.workspace_id == workspace_id,
                    DocumentDB.user_id == current_user["id"],
                    DocumentDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            document_db = result.scalar_one_or_none()

            if not document_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            # Check if preview exists in metadata
            preview_path = None
            if document_db.doc_metadata and "preview_path" in document_db.doc_metadata:
                preview_path = document_db.doc_metadata["preview_path"]

            if preview_path:
                full_preview_path = os.path.join(settings.UPLOAD_DIR, preview_path)
                if os.path.exists(full_preview_path):
                    return FileResponse(
                        path=full_preview_path,
                        media_type="image/png",
                        filename=f"preview_{document_db.original_filename}.png",
                    )

            # No preview available
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preview not available for this document",
            )

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # Fallback to in-memory storage
        try:
            doc_id = int(str(document_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        for doc in DOCUMENTS_DB:
            if doc["id"] == doc_id and doc["user_id"] == current_user["id"]:
                preview_path = doc.get("preview_path")
                if preview_path:
                    full_preview_path = os.path.join(settings.UPLOAD_DIR, preview_path)
                    if os.path.exists(full_preview_path):
                        return FileResponse(
                            path=full_preview_path,
                            media_type="image/png",
                            filename=f"preview_{doc['original_filename']}.png",
                        )
                break

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not available for this document",
        )


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get extracted document content and metadata"""
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(DocumentDB).where(
                and_(
                    DocumentDB.id == document_id,
                    DocumentDB.workspace_id == workspace_id,
                    DocumentDB.user_id == current_user["id"],
                    DocumentDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            document_db = result.scalar_one_or_none()

            if not document_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            return {
                "document_id": document_db.id,
                "title": document_db.title,
                "original_filename": document_db.original_filename,
                "extracted_text": document_db.extracted_text or "",
                "metadata": document_db.doc_metadata or {},
                "status": document_db.status,
                "created_at": document_db.created_at,
                "updated_at": document_db.updated_at,
            }

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # Fallback to in-memory storage
        try:
            doc_id = int(str(document_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        for doc in DOCUMENTS_DB:
            if doc["id"] == doc_id and doc["user_id"] == current_user["id"]:
                return {
                    "document_id": doc["id"],
                    "title": doc["title"],
                    "original_filename": doc["original_filename"],
                    "extracted_text": doc.get("extracted_text", ""),
                    "metadata": doc.get("metadata", {}),
                    "status": doc["status"],
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(DocumentDB).where(
                and_(
                    DocumentDB.id == document_id,
                    DocumentDB.workspace_id == workspace_id,
                    DocumentDB.user_id == current_user["id"],
                    DocumentDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            document_db = result.scalar_one_or_none()

            if not document_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            # Soft delete (mark as deleted)
            document_db.deleted_at = datetime.utcnow()
            document_db.deleted_by = current_user["id"]

            await db.commit()

            # Optionally delete physical file
            if os.path.exists(document_db.file_path):
                os.remove(document_db.file_path)

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # Fallback to in-memory storage
        try:
            doc_id = int(str(document_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        for i, doc in enumerate(DOCUMENTS_DB):
            if doc["id"] == doc_id and doc["user_id"] == current_user["id"]:
                # Delete the file
                if os.path.exists(doc["file_path"]):
                    os.remove(doc["file_path"])

                # Remove document from db
                DOCUMENTS_DB.pop(i)
                return

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
