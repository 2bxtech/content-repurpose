"""
Monitoring Dashboard API Endpoints

Provides real-time monitoring data, metrics dashboards, and system insights.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.services.metrics_service import metrics_collector, performance_monitor
from app.services.health_monitoring import health_monitor
from app.services.audit_service import audit_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Mock auth dependency for now - replace with actual auth implementation
async def get_current_user():
    return {"email": "admin@example.com", "id": "admin"}


class DashboardTimeRange(BaseModel):
    start_time: datetime
    end_time: datetime
    interval: str = "1h"  # 1m, 5m, 15m, 1h, 1d


@router.get("/monitoring/dashboard/overview")
async def get_dashboard_overview(
    current_user = Depends(get_current_user)
):
    """Get high-level dashboard overview"""
    try:
        # Get current system health
        health_status = await health_monitor.get_system_health()
        
        # Get performance summary
        performance_summary = await performance_monitor.get_performance_summary()
        
        # Get key metrics
        key_metrics = await metrics_collector.get_dashboard_metrics()
        
        # Get recent alerts
        active_alerts = await performance_monitor.get_active_alerts()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "system_health": health_status,
                "performance": performance_summary,
                "key_metrics": key_metrics,
                "active_alerts": len(active_alerts),
                "alerts": active_alerts[:5]  # Show top 5 alerts
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get dashboard overview",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/metrics")
async def get_dashboard_metrics(
    time_range: str = Query("1h", regex="^(15m|1h|6h|24h|7d|30d)$"),
    metric_types: Optional[List[str]] = Query(None),
    current_user = Depends(get_current_user)
):
    """Get detailed metrics for dashboard charts"""
    try:
        # Parse time range
        time_delta_map = {
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        end_time = datetime.now()
        start_time = end_time - time_delta_map[time_range]
        
        # Get metrics from collector
        metrics_data = await metrics_collector.get_metrics_for_timerange(
            start_time=start_time,
            end_time=end_time,
            metric_types=metric_types
        )
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration": time_range
            },
            "metrics": metrics_data
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get dashboard metrics",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/ai-usage")
async def get_ai_usage_dashboard(
    time_range: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$"),
    current_user = Depends(get_current_user)
):
    """Get AI usage metrics and cost analytics"""
    try:
        # Parse time range
        time_delta_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        end_time = datetime.now()
        start_time = end_time - time_delta_map[time_range]
        
        # Get AI usage metrics
        ai_metrics = await metrics_collector.get_ai_usage_metrics(
            start_time=start_time,
            end_time=end_time
        )
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration": time_range
            },
            "ai_usage": ai_metrics
        }
    
    except Exception as e:
        logger.error(f"Failed to get AI usage dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get AI usage dashboard",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/performance")
async def get_performance_dashboard(
    time_range: str = Query("1h", regex="^(15m|1h|6h|24h)$"),
    current_user = Depends(get_current_user)
):
    """Get system performance metrics dashboard"""
    try:
        # Get performance metrics
        performance_data = await performance_monitor.get_performance_dashboard(time_range)
        
        return {
            "status": "success",
            "performance": performance_data
        }
    
    except Exception as e:
        logger.error(f"Failed to get performance dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get performance dashboard",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/security")
async def get_security_dashboard(
    time_range: str = Query("24h", regex="^(1h|6h|24h|7d)$"),
    current_user = Depends(get_current_user)
):
    """Get security monitoring dashboard"""
    try:
        # Parse time range
        time_delta_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7)
        }
        
        end_time = datetime.now()
        start_time = end_time - time_delta_map[time_range]
        
        # Get security events
        security_events = await audit_service.get_security_events(
            start_time=start_time,
            end_time=end_time
        )
        
        # Get security metrics
        security_metrics = await audit_service.get_security_metrics()
        
        return {
            "status": "success",
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration": time_range
            },
            "security": {
                "events": security_events,
                "metrics": security_metrics
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get security dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get security dashboard",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/alerts")
async def get_alerts_dashboard(
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    status: Optional[str] = Query(None, regex="^(active|resolved|acknowledged)$"),
    current_user = Depends(get_current_user)
):
    """Get alerts management dashboard"""
    try:
        # Get alerts with filters
        alerts = await performance_monitor.get_alerts_dashboard(
            severity=severity,
            status=status
        )
        
        return {
            "status": "success",
            "alerts": alerts
        }
    
    except Exception as e:
        logger.error(f"Failed to get alerts dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get alerts dashboard",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/realtime")
async def get_realtime_metrics(
    current_user = Depends(get_current_user)
):
    """Get real-time system metrics"""
    try:
        # Get current system state
        realtime_data = {
            "timestamp": datetime.now().isoformat(),
            "system": await health_monitor.get_real_time_metrics(),
            "active_connections": await metrics_collector.get_active_connections(),
            "current_load": await performance_monitor.get_current_load(),
            "memory_usage": await performance_monitor.get_memory_usage(),
            "recent_errors": await audit_service.get_recent_errors(limit=10)
        }
        
        return {
            "status": "success",
            "realtime": realtime_data
        }
    
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get real-time metrics",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/export")
async def export_dashboard_data(
    format: str = Query("json", regex="^(json|csv|xlsx)$"),
    time_range: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$"),
    data_types: Optional[List[str]] = Query(None),
    current_user = Depends(get_current_user)
):
    """Export dashboard data in various formats"""
    try:
        # Parse time range
        time_delta_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        end_time = datetime.now()
        start_time = end_time - time_delta_map[time_range]
        
        # Collect data based on requested types
        export_data = {}
        
        if not data_types or "metrics" in data_types:
            export_data["metrics"] = await metrics_collector.get_metrics_for_timerange(
                start_time=start_time,
                end_time=end_time
            )
        
        if not data_types or "audit" in data_types:
            export_data["audit_events"] = await audit_service.get_events_for_export(
                start_time=start_time,
                end_time=end_time
            )
        
        if not data_types or "alerts" in data_types:
            export_data["alerts"] = await performance_monitor.get_alerts_for_export(
                start_time=start_time,
                end_time=end_time
            )
        
        # Format data based on requested format
        if format == "json":
            return {
                "status": "success",
                "format": "json",
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "data": export_data
            }
        else:
            # For CSV/XLSX, return metadata and instructions
            return {
                "status": "success",
                "format": format,
                "message": f"Data export in {format} format prepared",
                "download_url": f"/monitoring/dashboard/download/{format}",
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            }
    
    except Exception as e:
        logger.error(f"Failed to export dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to export dashboard data",
                "error": str(e)
            }
        )


@router.get("/monitoring/dashboard/config")
async def get_dashboard_config(
    current_user = Depends(get_current_user)
):
    """Get dashboard configuration and customization options"""
    try:
        config = {
            "refresh_intervals": {
                "realtime": 5,  # seconds
                "metrics": 30,
                "alerts": 60,
                "health": 120
            },
            "chart_options": {
                "time_ranges": ["15m", "1h", "6h", "24h", "7d", "30d"],
                "metric_types": [
                    "api_requests",
                    "response_times",
                    "error_rates",
                    "ai_usage",
                    "costs",
                    "system_resources"
                ],
                "chart_types": ["line", "bar", "area", "pie", "gauge"]
            },
            "alert_settings": {
                "severity_levels": ["low", "medium", "high", "critical"],
                "notification_channels": ["email", "webhook", "dashboard"],
                "auto_refresh": True
            },
            "export_formats": ["json", "csv", "xlsx"],
            "security": {
                "audit_retention_days": 90,
                "max_export_records": 10000,
                "require_auth": True
            }
        }
        
        return {
            "status": "success",
            "configuration": config
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Failed to get dashboard configuration",
                "error": str(e)
            }
        )