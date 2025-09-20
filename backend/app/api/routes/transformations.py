"""
Production Transformations Router
Fixed to eliminate SQLAlchemy greenlet errors with proper async patterns
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid
import logging

from app.models.transformation import (
    Transformation,
    TransformationCreate,
    TransformationList,
    TransformationStatus,
    TransformationType,
)
from app.db.models.transformation import Transformation as TransformationDB
from app.db.models.document import Document as DocumentDB
from app.db.models.workspace import Workspace
from app.api.routes.auth import get_current_active_user
from app.api.routes.workspaces import get_current_workspace_context
from app.core.database import get_db_session
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=Transformation, status_code=status.HTTP_201_CREATED)
async def create_transformation(
    transformation: TransformationCreate,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new content transformation
    Fixed to eliminate greenlet errors with proper async patterns
    """
    try:
        user_id = uuid.UUID(current_user["id"])
        workspace_id = workspace_context["workspace_id"]
        
        logger.info(f"Creating transformation: user_id={user_id}, workspace_id={workspace_id}, document_id={transformation.document_id}")
        
        if not db:
            # Fallback for in-memory mode
            return await _create_transformation_in_memory(transformation, user_id)
        
        # Get workspace using explicit async queries (no RLS complexity)
        
        # Verify document exists with eager loading to prevent lazy loading issues
        doc_stmt = (
            select(DocumentDB)
            .where(
                and_(
                    DocumentDB.id == transformation.document_id,
                    DocumentDB.user_id == uuid.UUID(current_user["id"]),  # Explicit UUID conversion
                    DocumentDB.deleted_at.is_(None)
                )
            )
            .options(
                selectinload(DocumentDB.workspace),  # Eager load relationships
                selectinload(DocumentDB.user)
            )
        )
        
        doc_result = await db.execute(doc_stmt)
        document = doc_result.unique().scalar_one_or_none()
        
        logger.info(f"Document lookup result: {document}")
        if document:
            logger.info(f"Found document: id={document.id}, user_id={document.user_id}, workspace_id={getattr(document, 'workspace_id', 'NO_WORKSPACE_ID')}")
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        # Create transformation with immediate completion (demo mode)
        transformation_data = {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "document_id": transformation.document_id,
            "transformation_type": transformation.transformation_type,
            "parameters": transformation.parameters or {},
            "status": TransformationStatus.COMPLETED,
            "result": _generate_demo_result(transformation, document),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        transformation_db = TransformationDB(**transformation_data)
        db.add(transformation_db)
        
        await db.commit()
        await db.refresh(transformation_db)
        
        # Return response model
        return Transformation(
            id=uuid.UUID(str(transformation_db.id)),
            user_id=uuid.UUID(str(transformation_db.user_id)),
            document_id=uuid.UUID(str(transformation_db.document_id)),
            transformation_type=transformation_db.transformation_type,
            parameters=transformation_db.parameters,
            status=transformation_db.status,
            result=transformation_db.result,
            task_id=None,
            created_at=transformation_db.created_at,
            updated_at=transformation_db.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transformation: {str(e)}")
        if db:
            await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transformation: {str(e)}"
        )

def _generate_demo_result(transformation: TransformationCreate, document) -> str:
    """Generate demo transformation result"""
    transform_type = transformation.transformation_type.value
    doc_name = getattr(document, 'filename', 'document')
    
    results = {
        'SUMMARY': f"**Summary of {doc_name}**\n\nThis is a comprehensive summary demonstrating your content repurposing system. The original document has been analyzed and key points extracted to create this concise overview. This shows the successful integration of your FastAPI backend with document processing capabilities.",
        
        'BLOG_POST': f"**{doc_name} - Blog Post**\n\n# Transform Your Content with AI\n\nThis blog post demonstrates the successful transformation of your uploaded document into engaging blog content. Your content repurposing system successfully processed the original material and created this formatted blog post.\n\n## Key Features Demonstrated\n- Document upload and processing\n- AI-powered content transformation\n- Multi-format output generation\n\nThis showcases your technical expertise in building sophisticated content management systems.",
        
        'SOCIAL_MEDIA': f"**Social Media Posts from {doc_name}**\n\n📱 **LinkedIn Post:**\nJust transformed content using an advanced AI system! This demonstrates sophisticated document processing and content repurposing capabilities. #AI #ContentCreation #TechShowcase\n\n🐦 **Twitter Post:**\nBuilding amazing content transformation tools! This post was generated from uploaded documents using FastAPI + AI. #TechStack #Innovation\n\n📘 **Facebook Post:**\nExcited to share this content transformation demo! This system showcases document processing, AI integration, and multi-format content generation.",
        
        'EMAIL_SEQUENCE': f"**Email Sequence from {doc_name}**\n\n**Email 1: Introduction**\nSubject: Welcome to Content Transformation\n\nHi there!\n\nThis email demonstrates the successful processing of your document through our content repurposing system...\n\n**Email 2: Deep Dive**\nSubject: Exploring Your Content Further\n\nBuilding on our previous communication, this email shows advanced content transformation capabilities...\n\n**Email 3: Call to Action**\nSubject: Ready to Transform More Content?\n\nThis sequence demonstrates the complete content transformation pipeline from document upload to multi-format output generation.",
        
        'NEWSLETTER': f"**Newsletter: {doc_name} Edition**\n\n# Content Transformation Weekly\n\n## Featured Article\nThis newsletter demonstrates the successful transformation of your uploaded document into a professional newsletter format.\n\n## Tech Highlights\n- FastAPI backend implementation\n- Async SQLAlchemy integration\n- Multi-tenant architecture\n- Document processing pipeline\n\n## What's Next\nThis system showcases enterprise-grade content management and AI integration capabilities.",
        
        'CUSTOM': f"**Custom Transformation of {doc_name}**\n\nThis custom transformation demonstrates the flexibility of your content repurposing system. The original document has been processed according to custom parameters, showing the adaptability and sophistication of your technical implementation.\n\nKey technical achievements:\n- Robust async architecture\n- Scalable database design\n- Flexible transformation engine\n- Production-ready error handling"
    }
    
    return results.get(transform_type, f"Successfully transformed {doc_name} using {transform_type} format. This demonstrates your content repurposing system's capabilities.")

async def _create_transformation_in_memory(transformation: TransformationCreate, user_id: uuid.UUID) -> Transformation:
    """Fallback in-memory transformation creation"""
    return Transformation(
        id=uuid.uuid4(),
        user_id=user_id,
        document_id=transformation.document_id,
        transformation_type=transformation.transformation_type,
        parameters=transformation.parameters,
        status=TransformationStatus.COMPLETED,
        result=f"In-memory demo transformation ({transformation.transformation_type.value}) completed successfully!",
        task_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

@router.get("/debug/workspace-test")
async def debug_workspace_test():
    """Debug endpoint to test Workspace model access"""
    try:
        logger.info("Testing Workspace class access...")
        logger.info(f"Workspace: {Workspace}")
        logger.info(f"Workspace.__name__: {Workspace.__name__}")
        logger.info(f"Workspace.__table__.name: {Workspace.__table__.name}")
        logger.info(f"Workspace columns: {[c.name for c in Workspace.__table__.columns]}")
        return {"status": "success", "message": "Workspace model accessible"}
    except Exception as e:
        logger.error(f"Error accessing Workspace: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

@router.get("/", response_model=TransformationList)
async def get_user_transformations(
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get user transformations with proper eager loading"""
    try:
        user_id = uuid.UUID(current_user["id"])
        workspace_id = workspace_context["workspace_id"]
        
        if not db:
            return TransformationList(transformations=[], count=0)
        
        # Use minimal query without eager loading to isolate the issue
        stmt = (
            select(TransformationDB)
            .where(
                and_(
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == user_id,
                    TransformationDB.deleted_at.is_(None),
                )
            )
            # Remove all eager loading temporarily
            # .options(
            #     selectinload(TransformationDB.document),
            #     # Temporarily remove workspace loading to test
            #     # selectinload(TransformationDB.workspace)
            # )
            .order_by(TransformationDB.created_at.desc())
        )
        
        result = await db.execute(stmt)
        transformations_db = result.unique().scalars().all()
        
        transformations = [
            Transformation(
                id=uuid.UUID(str(t.id)),
                user_id=uuid.UUID(str(t.user_id)),
                document_id=uuid.UUID(str(t.document_id)),
                transformation_type=t.transformation_type,
                parameters=t.parameters,
                status=t.status,
                result=t.result,
                task_id=getattr(t, 'task_id', None),
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in transformations_db
        ]
        
        return TransformationList(transformations=transformations, count=len(transformations))
        
    except Exception as e:
        logger.error(f"Error retrieving transformations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transformations"
        )

@router.get("/{transformation_id}", response_model=Transformation)
async def get_transformation(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get specific transformation with eager loading"""
    try:
        user_id = uuid.UUID(current_user["id"])
        workspace_id = workspace_context["workspace_id"]
        
        if not db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transformation not found"
            )
        
        stmt = (
            select(TransformationDB)
            .where(
                and_(
                    TransformationDB.id == transformation_id,
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == user_id,
                    TransformationDB.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(TransformationDB.document),
                selectinload(TransformationDB.workspace)
            )
        )
        
        result = await db.execute(stmt)
        transformation_db = result.unique().scalar_one_or_none()
        
        if not transformation_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transformation not found",
            )
        
        return Transformation(
            id=uuid.UUID(str(transformation_db.id)),
            user_id=uuid.UUID(str(transformation_db.user_id)),
            document_id=uuid.UUID(str(transformation_db.document_id)),
            transformation_type=transformation_db.transformation_type,
            parameters=transformation_db.parameters,
            status=transformation_db.status,
            result=transformation_db.result,
            task_id=getattr(transformation_db, 'task_id', None),
            created_at=transformation_db.created_at,
            updated_at=transformation_db.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transformation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transformation"
        )

@router.get("/types/available")
async def get_available_transformation_types(
    current_user: dict = Depends(get_current_active_user)
):
    """Get available transformation types"""
    return {
        "transformation_types": [
            {
                "type": TransformationType.SUMMARY.value,
                "description": "Create a concise summary of the document content",
                "parameters": ["length", "style"]
            },
            {
                "type": TransformationType.BLOG_POST.value,
                "description": "Transform content into a blog post format",
                "parameters": ["tone", "target_audience", "word_count"]
            },
            {
                "type": TransformationType.SOCIAL_MEDIA.value,
                "description": "Create social media posts from content",
                "parameters": ["platform", "tone", "hashtags"]
            },
            {
                "type": TransformationType.EMAIL_SEQUENCE.value,
                "description": "Generate email sequence from content",
                "parameters": ["sequence_length", "tone", "call_to_action"]
            },
            {
                "type": TransformationType.NEWSLETTER.value,
                "description": "Format content as newsletter",
                "parameters": ["sections", "tone", "length"]
            },
            {
                "type": TransformationType.CUSTOM.value,
                "description": "Custom transformation with specific instructions",
                "parameters": ["instructions", "format", "tone"]
            }
        ],
        "count": 6
    }

# Debug endpoints (simplified)
@router.get("/debug/user-stats")
async def get_user_transformation_stats(
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get transformation stats with proper async queries"""
    try:
        user_id = uuid.UUID(current_user["id"])
        workspace_id = workspace_context["workspace_id"]
        
        if not db:
            return {"message": "Database not available", "mode": "in_memory"}
        
        # Count by status using explicit async query
        status_stmt = (
            select(
                TransformationDB.status,
                func.count(TransformationDB.id).label('count')
            )
            .where(
                and_(
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == user_id,
                    TransformationDB.deleted_at.is_(None),
                )
            )
            .group_by(TransformationDB.status)
        )
        
        status_result = await db.execute(status_stmt)
        status_counts = {row.status.value: row.count for row in status_result}
        
        return {
            "user_id": str(user_id),
            "workspace_id": str(workspace_id),
            "transformations_by_status": status_counts,
            "mode": "database"
        }
        
    except Exception as e:
        logger.error(f"Error getting transformation stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transformation statistics"
        )

# CORS OPTIONS handlers
@router.options("/")
@router.options("/{path:path}")
async def handle_cors_options():
    """Handle CORS preflight requests"""
    return {"message": "OK"}