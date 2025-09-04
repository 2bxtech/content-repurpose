"""
Security Management API Endpoints

Provides endpoints for security monitoring, audit logs, secret management,
and security configuration.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.services.audit_service import audit_service, AuditEventType, AuditLevel
from app.services.secret_management import secret_manager, SecretType
from app.core.config import settings
import logging


# Mock auth dependency for now - replace with actual auth implementation
async def get_current_user():
    return {"email": "admin@example.com", "id": "admin"}


router = APIRouter()
logger = logging.getLogger(__name__)


class SecretCreateRequest(BaseModel):
    name: str
    value: str
    secret_type: SecretType
    description: Optional[str] = None
    rotation_policy_days: Optional[int] = None


class SecretUpdateRequest(BaseModel):
    value: str


@router.get("/security/audit/events")
async def get_audit_events(
    limit: int = 100,
    event_type: Optional[str] = None,
    level: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Get audit events with optional filtering"""
    try:
        # Convert string parameters to enums if provided
        audit_event_type = None
        if event_type:
            try:
                audit_event_type = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event_type: {event_type}",
                )

        audit_level = None
        if level:
            try:
                audit_level = AuditLevel(level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid level: {level}",
                )

        # Get audit events
        events = await audit_service.get_recent_events(
            limit=limit, event_type=audit_event_type, user_id=user_id, level=audit_level
        )

        return {
            "status": "success",
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "user_id": event.user_id,
                    "workspace_id": event.workspace_id,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "resource_type": event.resource_type,
                    "resource_id": event.resource_id,
                    "action": event.action,
                    "outcome": event.outcome,
                    "details": event.details,
                    "security_context": event.security_context,
                    "performance_metrics": event.performance_metrics,
                    "cost_metrics": event.cost_metrics,
                    "error_details": event.error_details,
                }
                for event in events
            ],
            "count": len(events),
            "filters_applied": {
                "event_type": event_type,
                "level": level,
                "user_id": user_id,
                "limit": limit,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to retrieve audit events",
                "error": str(e),
            },
        )


@router.get("/security/audit/metrics")
async def get_audit_metrics(current_user=Depends(get_current_user)):
    """Get audit metrics and statistics"""
    try:
        metrics = await audit_service.get_audit_metrics()

        return {"status": "success", "metrics": metrics}

    except Exception as e:
        logger.error(f"Failed to get audit metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to retrieve audit metrics",
                "error": str(e),
            },
        )


@router.get("/security/secrets")
async def list_secrets(
    include_expired: bool = False, current_user=Depends(get_current_user)
):
    """List all managed secrets (metadata only)"""
    try:
        secrets_list = secret_manager.list_secrets(include_expired=include_expired)

        return {
            "status": "success",
            "secrets": [
                {
                    "secret_id": secret.secret_id,
                    "name": secret.name,
                    "secret_type": secret.secret_type,
                    "status": secret.status,
                    "created_at": secret.created_at,
                    "expires_at": secret.expires_at,
                    "last_rotated": secret.last_rotated,
                    "last_accessed": secret.last_accessed,
                    "access_count": secret.access_count,
                    "rotation_policy_days": secret.rotation_policy_days,
                    "description": secret.description,
                }
                for secret in secrets_list
            ],
            "count": len(secrets_list),
        }

    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to list secrets",
                "error": str(e),
            },
        )


@router.post("/security/secrets")
async def create_secret(
    secret_request: SecretCreateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    """Create a new managed secret"""
    try:
        secret_id = await secret_manager.store_secret(
            name=secret_request.name,
            value=secret_request.value,
            secret_type=secret_request.secret_type,
            description=secret_request.description,
            rotation_policy_days=secret_request.rotation_policy_days,
            accessed_by=current_user.get("email"),
        )

        return {
            "status": "success",
            "secret_id": secret_id,
            "message": f"Secret '{secret_request.name}' created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to create secret",
                "error": str(e),
            },
        )


@router.put("/security/secrets/{secret_id}/rotate")
async def rotate_secret(
    secret_id: str,
    secret_request: SecretUpdateRequest,
    request: Request,
    current_user=Depends(get_current_user),
):
    """Rotate a secret to a new value"""
    try:
        success = await secret_manager.rotate_secret(
            secret_id=secret_id,
            new_value=secret_request.value,
            accessed_by=current_user.get("email"),
        )

        if success:
            return {
                "status": "success",
                "message": f"Secret {secret_id} rotated successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": f"Secret {secret_id} not found"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate secret {secret_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to rotate secret",
                "error": str(e),
            },
        )


@router.put("/security/secrets/{secret_id}/compromise")
async def mark_secret_compromised(
    secret_id: str, request: Request, current_user=Depends(get_current_user)
):
    """Mark a secret as compromised"""
    try:
        success = await secret_manager.mark_compromised(
            secret_id=secret_id, accessed_by=current_user.get("email")
        )

        if success:
            return {
                "status": "success",
                "message": f"Secret {secret_id} marked as compromised",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": f"Secret {secret_id} not found"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark secret {secret_id} as compromised: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to mark secret as compromised",
                "error": str(e),
            },
        )


@router.delete("/security/secrets/{secret_id}")
async def delete_secret(
    secret_id: str, request: Request, current_user=Depends(get_current_user)
):
    """Delete a secret permanently"""
    try:
        success = await secret_manager.delete_secret(
            secret_id=secret_id, accessed_by=current_user.get("email")
        )

        if success:
            return {
                "status": "success",
                "message": f"Secret {secret_id} deleted successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": f"Secret {secret_id} not found"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete secret {secret_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to delete secret",
                "error": str(e),
            },
        )


@router.get("/security/secrets/rotation-required")
async def get_secrets_requiring_rotation(
    days_ahead: int = 7, current_user=Depends(get_current_user)
):
    """Get secrets that require rotation within specified days"""
    try:
        requiring_rotation = secret_manager.get_secrets_requiring_rotation(days_ahead)

        return {
            "status": "success",
            "secrets": [
                {
                    "secret_id": secret.secret_id,
                    "name": secret.name,
                    "secret_type": secret.secret_type,
                    "expires_at": secret.expires_at,
                    "days_until_expiry": (
                        datetime.fromisoformat(secret.expires_at) - datetime.now()
                    ).days
                    if secret.expires_at
                    else None,
                }
                for secret in requiring_rotation
            ],
            "count": len(requiring_rotation),
            "days_ahead": days_ahead,
        }

    except Exception as e:
        logger.error(f"Failed to get secrets requiring rotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get secrets requiring rotation",
                "error": str(e),
            },
        )


@router.get("/security/analytics")
async def get_security_analytics(current_user=Depends(get_current_user)):
    """Get comprehensive security analytics"""
    try:
        # Get secret analytics
        secret_analytics = await secret_manager.get_secret_analytics()

        # Get audit metrics
        audit_metrics = await audit_service.get_audit_metrics()

        return {
            "status": "success",
            "analytics": {
                "secrets": secret_analytics,
                "audit": audit_metrics,
                "timestamp": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get security analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get security analytics",
                "error": str(e),
            },
        )


@router.get("/security/config")
async def get_security_configuration(current_user=Depends(get_current_user)):
    """Get current security configuration and policies"""
    try:
        from app.middleware.security import SecurityConfig

        config = SecurityConfig()

        return {
            "status": "success",
            "configuration": {
                "csp_policy": config.CSP_POLICY,
                "security_headers": config.SECURITY_HEADERS,
                "hsts_max_age": config.HSTS_MAX_AGE,
                "max_security_violations_per_minute": config.MAX_SECURITY_VIOLATIONS_PER_MINUTE,
                "max_validation_failures_per_minute": config.MAX_VALIDATION_FAILURES_PER_MINUTE,
                "environment": getattr(settings, "ENVIRONMENT", "development"),
                "debug_mode": getattr(settings, "DEBUG", False),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get security configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get security configuration",
                "error": str(e),
            },
        )
