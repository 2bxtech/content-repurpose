from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic
import os
import uuid

from app.models.transformations import (
    Transformation, TransformationCreate, TransformationList,
    TransformationType, TransformationStatus
)
from app.db.models.transformation import Transformation as TransformationDB
from app.db.models.document import Document as DocumentDB
from app.api.routes.auth import get_current_active_user
from app.api.routes.workspaces import get_current_workspace_context
from app.core.database import get_db_session
from app.core.config import settings
from app.services.workspace_service import workspace_service

# Mock database for transformations - will be replaced when DB is connected
TRANSFORMATIONS_DB = []
transformation_id_counter = 1

router = APIRouter()

def get_document_by_id(document_id: int, user_id: int):
    """Legacy function for in-memory mode"""
    from app.api.routes.documents import DOCUMENTS_DB
    for doc in DOCUMENTS_DB:
        if doc["id"] == document_id and doc["user_id"] == user_id:
            return doc
    return None

async def get_document_by_uuid(db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID, workspace_id: uuid.UUID):
    """Get document by UUID for database mode"""
    if not db:
        return None
    
    await workspace_service.set_workspace_context(db, workspace_id)
    
    try:
        stmt = (
            select(DocumentDB)
            .where(
                and_(
                    DocumentDB.id == document_id,
                    DocumentDB.workspace_id == workspace_id,
                    DocumentDB.user_id == user_id,
                    DocumentDB.deleted_at.is_(None)
                )
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    finally:
        await workspace_service.clear_workspace_context(db)

async def process_transformation(transformation_id: uuid.UUID, document_path: str, transformation_type: TransformationType, parameters: Dict[str, Any], db: AsyncSession = None):
    """
    Background task to process the transformation using Claude API
    """
    if db:
        # Database mode
        stmt = select(TransformationDB).where(TransformationDB.id == transformation_id)
        result = await db.execute(stmt)
        transformation = result.scalar_one_or_none()
        
        if not transformation:
            return
        
        # Set workspace context
        await workspace_service.set_workspace_context(db, transformation.workspace_id)
    else:
        # In-memory mode
        transformation = None
        for t in TRANSFORMATIONS_DB:
            if str(t["id"]) == str(transformation_id):
                transformation = t
                break
        
        if not transformation:
            return
    
    # Update status to processing
    if db:
        transformation.status = TransformationStatus.PROCESSING
        transformation.updated_at = datetime.utcnow()
        await db.commit()
    else:
        transformation["status"] = TransformationStatus.PROCESSING
        transformation["updated_at"] = datetime.now()
    
    try:
        # Read document content
        with open(document_path, "r", encoding="utf-8") as file:
            document_content = file.read()
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        
        # Prepare the prompt based on transformation type
        prompt = get_transformation_prompt(transformation_type, document_content, parameters)
        
        # Call Claude API
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.7,
            system="You are an expert content repurposing assistant. Your task is to transform the provided content into the requested format while maintaining the key information and adapting the style appropriately.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Update transformation with result
        if db:
            transformation.result = message.content[0].text
            transformation.status = TransformationStatus.COMPLETED
            transformation.updated_at = datetime.utcnow()
            transformation.ai_provider = "claude"
            transformation.tokens_used = message.usage.input_tokens + message.usage.output_tokens if hasattr(message, 'usage') else None
            await db.commit()
        else:
            transformation["result"] = message.content[0].text
            transformation["status"] = TransformationStatus.COMPLETED
            transformation["updated_at"] = datetime.now()
        
    except Exception as e:
        # Update transformation with error
        if db:
            transformation.status = TransformationStatus.FAILED
            transformation.error_message = f"Error processing transformation: {str(e)}"
            transformation.updated_at = datetime.utcnow()
            await db.commit()
        else:
            transformation["status"] = TransformationStatus.FAILED
            transformation["result"] = f"Error processing transformation: {str(e)}"
            transformation["updated_at"] = datetime.now()
    
    finally:
        if db:
            await workspace_service.clear_workspace_context(db)

def get_transformation_prompt(transformation_type: TransformationType, document_content: str, parameters: Dict[str, Any]) -> str:
    """
    Generate a prompt for Claude based on the transformation type
    """
    base_prompt = f"Here is the original content:\n\n{document_content}\n\n"
    
    if transformation_type == TransformationType.BLOG_POST:
        prompt = base_prompt + "Transform this content into a well-structured blog post. "
        if "word_count" in parameters:
            prompt += f"The target word count is around {parameters['word_count']} words. "
        if "tone" in parameters:
            prompt += f"Use a {parameters['tone']} tone. "
        prompt += "Include a catchy title, introduction, main sections with subheadings, and a conclusion."
        
    elif transformation_type == TransformationType.SOCIAL_MEDIA:
        platform = parameters.get("platform", "general")
        prompt = base_prompt + f"Create social media content for {platform} based on this information. "
        if "post_count" in parameters:
            prompt += f"Generate {parameters['post_count']} distinct posts. "
        prompt += "Each post should be engaging, concise, and include relevant hashtags."
        
    elif transformation_type == TransformationType.EMAIL_SEQUENCE:
        prompt = base_prompt + "Transform this content into an email sequence. "
        if "email_count" in parameters:
            prompt += f"Create a series of {parameters['email_count']} emails. "
        prompt += "Include subject lines and email body content. Each email should have a clear purpose, engaging opening, valuable content, and a strong call-to-action."
        
    elif transformation_type == TransformationType.NEWSLETTER:
        prompt = base_prompt + "Convert this content into a newsletter format. "
        if "sections" in parameters:
            prompt += f"Include the following sections: {', '.join(parameters['sections'])}. "
        prompt += "The newsletter should have a clear structure, engaging introduction, main content sections, and a conclusion with next steps or call-to-action."
        
    elif transformation_type == TransformationType.SUMMARY:
        prompt = base_prompt + "Create a concise summary of this content. "
        if "length" in parameters:
            prompt += f"The summary should be approximately {parameters['length']} words. "
        prompt += "Capture the key points, main arguments, and essential information while maintaining clarity."
        
    else:  # CUSTOM or fallback
        prompt = base_prompt + parameters.get("custom_instructions", "Transform this content into a new format while preserving the key information.")
    
    return prompt

@router.post("/transformations", response_model=Transformation, status_code=status.HTTP_201_CREATED)
async def create_transformation(
    transformation: TransformationCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session)
):
    global transformation_id_counter
    
    workspace_id = workspace_context["workspace_id"]
    
    # Check workspace limits for AI requests
    if db:
        can_create, error_msg = await workspace_service.check_workspace_limits(
            db, workspace_id, "ai_transform"
        )
        if not can_create:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    if db:
        # Database mode - validate document exists and belongs to user in workspace
        document = await get_document_by_uuid(db, transformation.document_id, current_user["id"], workspace_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Set workspace context
        await workspace_service.set_workspace_context(db, workspace_id)
        
        try:
            # Create transformation record
            transformation_db = TransformationDB(
                workspace_id=workspace_id,
                user_id=current_user["id"],
                document_id=transformation.document_id,
                transformation_type=transformation.transformation_type,
                parameters=transformation.parameters,
                status=TransformationStatus.PENDING,
                created_by=current_user["id"]
            )
            
            db.add(transformation_db)
            await db.commit()
            await db.refresh(transformation_db)
            
            # Start background task to process the transformation
            background_tasks.add_task(
                process_transformation,
                transformation_db.id,
                document.file_path,
                transformation.transformation_type,
                transformation.parameters,
                db
            )
            
            return Transformation(
                id=transformation_db.id,
                user_id=transformation_db.user_id,
                document_id=transformation_db.document_id,
                transformation_type=transformation_db.transformation_type,
                parameters=transformation_db.parameters,
                status=transformation_db.status,
                result=transformation_db.result,
                created_at=transformation_db.created_at,
                updated_at=transformation_db.updated_at
            )
        
        finally:
            await workspace_service.clear_workspace_context(db)
    
    else:
        # In-memory mode
        document = get_document_by_id(transformation.document_id, current_user["id"])
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Create transformation record
        new_transformation = {
            "id": transformation_id_counter,
            "user_id": current_user["id"],
            "document_id": transformation.document_id,
            "transformation_type": transformation.transformation_type,
            "parameters": transformation.parameters,
            "status": TransformationStatus.PENDING,
            "result": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        TRANSFORMATIONS_DB.append(new_transformation)
        transformation_id_counter += 1
        
        # Start background task to process the transformation
        background_tasks.add_task(
            process_transformation,
            new_transformation["id"],
            document["file_path"],
            transformation.transformation_type,
            transformation.parameters
        )
        
        return new_transformation

@router.get("/transformations", response_model=TransformationList)
async def get_user_transformations(
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session)
):
    workspace_id = workspace_context["workspace_id"]
    
    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)
        
        try:
            stmt = (
                select(TransformationDB)
                .where(
                    and_(
                        TransformationDB.workspace_id == workspace_id,
                        TransformationDB.user_id == current_user["id"],
                        TransformationDB.deleted_at.is_(None)
                    )
                )
                .order_by(TransformationDB.created_at.desc())
            )
            
            result = await db.execute(stmt)
            transformations_db = result.scalars().all()
            
            transformations = []
            for t_db in transformations_db:
                transformations.append(Transformation(
                    id=t_db.id,
                    user_id=t_db.user_id,
                    document_id=t_db.document_id,
                    transformation_type=t_db.transformation_type,
                    parameters=t_db.parameters,
                    status=t_db.status,
                    result=t_db.result,
                    created_at=t_db.created_at,
                    updated_at=t_db.updated_at
                ))
            
            return TransformationList(transformations=transformations, count=len(transformations))
        
        finally:
            await workspace_service.clear_workspace_context(db)
    
    else:
        # In-memory mode
        user_transformations = [t for t in TRANSFORMATIONS_DB if t["user_id"] == current_user["id"]]
        return TransformationList(transformations=user_transformations, count=len(user_transformations))

@router.get("/transformations/{transformation_id}", response_model=Transformation)
async def get_transformation(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session)
):
    workspace_id = workspace_context["workspace_id"]
    
    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)
        
        try:
            stmt = (
                select(TransformationDB)
                .where(
                    and_(
                        TransformationDB.id == transformation_id,
                        TransformationDB.workspace_id == workspace_id,
                        TransformationDB.user_id == current_user["id"],
                        TransformationDB.deleted_at.is_(None)
                    )
                )
            )
            
            result = await db.execute(stmt)
            transformation_db = result.scalar_one_or_none()
            
            if not transformation_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation not found"
                )
            
            return Transformation(
                id=transformation_db.id,
                user_id=transformation_db.user_id,
                document_id=transformation_db.document_id,
                transformation_type=transformation_db.transformation_type,
                parameters=transformation_db.parameters,
                status=transformation_db.status,
                result=transformation_db.result,
                created_at=transformation_db.created_at,
                updated_at=transformation_db.updated_at
            )
        
        finally:
            await workspace_service.clear_workspace_context(db)
    
    else:
        # In-memory mode
        try:
            t_id = int(str(transformation_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transformation not found"
            )
        
        for transformation in TRANSFORMATIONS_DB:
            if transformation["id"] == t_id and transformation["user_id"] == current_user["id"]:
                return transformation
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transformation not found"
        )

@router.delete("/transformations/{transformation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transformation(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session)
):
    workspace_id = workspace_context["workspace_id"]
    
    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)
        
        try:
            stmt = (
                select(TransformationDB)
                .where(
                    and_(
                        TransformationDB.id == transformation_id,
                        TransformationDB.workspace_id == workspace_id,
                        TransformationDB.user_id == current_user["id"],
                        TransformationDB.deleted_at.is_(None)
                    )
                )
            )
            
            result = await db.execute(stmt)
            transformation_db = result.scalar_one_or_none()
            
            if not transformation_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation not found"
                )
            
            # Soft delete
            transformation_db.deleted_at = datetime.utcnow()
            transformation_db.deleted_by = current_user["id"]
            
            await db.commit()
        
        finally:
            await workspace_service.clear_workspace_context(db)
    
    else:
        # In-memory mode
        try:
            t_id = int(str(transformation_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transformation not found"
            )
        
        for i, transformation in enumerate(TRANSFORMATIONS_DB):
            if transformation["id"] == t_id and transformation["user_id"] == current_user["id"]:
                TRANSFORMATIONS_DB.pop(i)
                return
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transformation not found"
        )