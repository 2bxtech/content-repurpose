from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
import uuid

from app.models.transformations import (
    Transformation,
    TransformationCreate,
    TransformationList,
    TransformationStatus,
)
from app.db.models.transformation import Transformation as TransformationDB
from app.db.models.document import Document as DocumentDB
from app.api.routes.auth import get_current_active_user
from app.api.routes.workspaces import get_current_workspace_context
from app.core.database import get_db_session
from app.services.workspace_service import workspace_service
from app.services.task_service import task_service

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


async def get_document_by_uuid(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
):
    """Get document by UUID for database mode"""
    if not db:
        return None

    await workspace_service.set_workspace_context(db, workspace_id)

    try:
        stmt = select(DocumentDB).where(
            and_(
                DocumentDB.id == document_id,
                DocumentDB.workspace_id == workspace_id,
                DocumentDB.user_id == user_id,
                DocumentDB.deleted_at.is_(None),
            )
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    finally:
        await workspace_service.clear_workspace_context(db)


@router.post(
    "/transformations",
    response_model=Transformation,
    status_code=status.HTTP_201_CREATED,
)
async def create_transformation(
    transformation: TransformationCreate,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
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
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )

    if db:
        # Database mode - validate document exists and belongs to user in workspace
        document = await get_document_by_uuid(
            db, transformation.document_id, current_user["id"], workspace_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
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
                created_by=current_user["id"],
            )

            db.add(transformation_db)
            await db.commit()
            await db.refresh(transformation_db)

            # Start Celery background task to process the transformation
            task_id = task_service.start_transformation_task(
                transformation_db.id,
                document.file_path,
                transformation.transformation_type,
                transformation.parameters,
                workspace_id,
                current_user["id"],
            )

            # Store task ID in the transformation record for tracking
            transformation_db.task_id = task_id
            await db.commit()

            return Transformation(
                id=transformation_db.id,
                user_id=transformation_db.user_id,
                document_id=transformation_db.document_id,
                transformation_type=transformation_db.transformation_type,
                parameters=transformation_db.parameters,
                status=transformation_db.status,
                result=transformation_db.result,
                task_id=task_id,
                created_at=transformation_db.created_at,
                updated_at=transformation_db.updated_at,
            )

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # In-memory mode - simplified for backward compatibility
        document = get_document_by_id(transformation.document_id, current_user["id"])
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
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
            "task_id": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        TRANSFORMATIONS_DB.append(new_transformation)
        transformation_id_counter += 1

        # For in-memory mode, we'll simulate immediate processing
        # In production, this should also use Celery
        new_transformation["status"] = TransformationStatus.PROCESSING
        new_transformation["result"] = (
            "In-memory mode: Transformation processing not implemented with Celery"
        )
        new_transformation["status"] = TransformationStatus.COMPLETED

        return new_transformation


@router.get("/transformations", response_model=TransformationList)
async def get_user_transformations(
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
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
                        TransformationDB.deleted_at.is_(None),
                    )
                )
                .order_by(TransformationDB.created_at.desc())
            )

            result = await db.execute(stmt)
            transformations_db = result.scalars().all()

            transformations = []
            for t_db in transformations_db:
                transformations.append(
                    Transformation(
                        id=t_db.id,
                        user_id=t_db.user_id,
                        document_id=t_db.document_id,
                        transformation_type=t_db.transformation_type,
                        parameters=t_db.parameters,
                        status=t_db.status,
                        result=t_db.result,
                        created_at=t_db.created_at,
                        updated_at=t_db.updated_at,
                    )
                )

            return TransformationList(
                transformations=transformations, count=len(transformations)
            )

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # In-memory mode
        user_transformations = [
            t for t in TRANSFORMATIONS_DB if t["user_id"] == current_user["id"]
        ]
        return TransformationList(
            transformations=user_transformations, count=len(user_transformations)
        )


@router.get("/transformations/{transformation_id}", response_model=Transformation)
async def get_transformation(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(TransformationDB).where(
                and_(
                    TransformationDB.id == transformation_id,
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == current_user["id"],
                    TransformationDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            transformation_db = result.scalar_one_or_none()

            if not transformation_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation not found",
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
                updated_at=transformation_db.updated_at,
            )

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # In-memory mode
        try:
            t_id = int(str(transformation_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
            )

        for transformation in TRANSFORMATIONS_DB:
            if (
                transformation["id"] == t_id
                and transformation["user_id"] == current_user["id"]
            ):
                return transformation

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
        )


@router.delete(
    "/transformations/{transformation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_transformation(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Set workspace context for RLS
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(TransformationDB).where(
                and_(
                    TransformationDB.id == transformation_id,
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == current_user["id"],
                    TransformationDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            transformation_db = result.scalar_one_or_none()

            if not transformation_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation not found",
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
            )

        for i, transformation in enumerate(TRANSFORMATIONS_DB):
            if (
                transformation["id"] == t_id
                and transformation["user_id"] == current_user["id"]
            ):
                TRANSFORMATIONS_DB.pop(i)
                return

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
        )


@router.get("/transformations/{transformation_id}/status")
async def get_transformation_task_status(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get the real-time status of a transformation task
    """
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Get transformation from database
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(TransformationDB).where(
                and_(
                    TransformationDB.id == transformation_id,
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == current_user["id"],
                    TransformationDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            transformation_db = result.scalar_one_or_none()

            if not transformation_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation not found",
                )

            # Get task status if task_id exists
            task_status = None
            if transformation_db.task_id:
                task_status = task_service.get_task_status(transformation_db.task_id)

            return {
                "transformation_id": transformation_id,
                "database_status": transformation_db.status,
                "task_status": task_status,
                "result": transformation_db.result,
                "error_message": transformation_db.error_message,
                "updated_at": transformation_db.updated_at,
            }

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        # In-memory mode
        try:
            t_id = int(str(transformation_id))
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
            )

        for transformation in TRANSFORMATIONS_DB:
            if (
                transformation["id"] == t_id
                and transformation["user_id"] == current_user["id"]
            ):
                return {
                    "transformation_id": transformation_id,
                    "database_status": transformation["status"],
                    "task_status": None,
                    "result": transformation.get("result"),
                    "error_message": None,
                    "updated_at": transformation["updated_at"],
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transformation not found"
        )


@router.post("/transformations/{transformation_id}/cancel")
async def cancel_transformation_task(
    transformation_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    workspace_context: dict = Depends(get_current_workspace_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Cancel a running transformation task
    """
    workspace_id = workspace_context["workspace_id"]

    if db:
        # Get transformation from database
        await workspace_service.set_workspace_context(db, workspace_id)

        try:
            stmt = select(TransformationDB).where(
                and_(
                    TransformationDB.id == transformation_id,
                    TransformationDB.workspace_id == workspace_id,
                    TransformationDB.user_id == current_user["id"],
                    TransformationDB.deleted_at.is_(None),
                )
            )

            result = await db.execute(stmt)
            transformation_db = result.scalar_one_or_none()

            if not transformation_db:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation not found",
                )

            # Cancel task if it's running
            if transformation_db.task_id and transformation_db.status in [
                TransformationStatus.PENDING,
                TransformationStatus.PROCESSING,
            ]:
                cancel_result = task_service.cancel_task(transformation_db.task_id)

                # Update transformation status
                transformation_db.status = TransformationStatus.FAILED
                transformation_db.error_message = "Task cancelled by user"
                transformation_db.updated_at = datetime.utcnow()
                await db.commit()

                return {
                    "transformation_id": transformation_id,
                    "status": "cancelled",
                    "message": "Transformation task cancelled successfully",
                    "task_result": cancel_result,
                }
            else:
                return {
                    "transformation_id": transformation_id,
                    "status": "not_cancellable",
                    "message": f"Transformation cannot be cancelled (current status: {transformation_db.status})",
                }

        finally:
            await workspace_service.clear_workspace_context(db)

    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Task cancellation not available in in-memory mode",
        )


@router.get("/system/workers")
async def get_worker_status(current_user: dict = Depends(get_current_active_user)):
    """
    Get Celery worker status (admin endpoint)
    """
    # TODO: Add admin role check
    return task_service.get_worker_status()


@router.get("/system/queue")
async def get_queue_info(current_user: dict = Depends(get_current_active_user)):
    """
    Get task queue information (admin endpoint)
    """
    # TODO: Add admin role check
    return task_service.get_queue_info()
