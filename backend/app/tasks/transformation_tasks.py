"""
Celery tasks for AI transformation processing.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import anthropic
import openai
import asyncio
import httpx

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.transformations import TransformationType, TransformationStatus
from app.db.models.transformation import Transformation as TransformationDB
from app.db.models.document import Document as DocumentDB
from app.services.workspace_service import workspace_service


async def send_websocket_notification(
    workspace_id: str,
    user_id: str,
    transformation_id: str,
    message_type: str,
    data: Dict[str, Any]
):
    """
    Send WebSocket notification to user about transformation progress
    """
    try:
        # Prepare notification payload
        notification_data = {
            "type": message_type,
            "data": {
                "transformation_id": transformation_id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                **data
            },
            "target": "user",
            "target_id": user_id
        }
        
        # Send HTTP request to WebSocket broadcast endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8000/api/ws/broadcast",
                json=notification_data,
                timeout=5.0
            )
            
            if response.status_code == 200:
                print(f"WebSocket notification sent: {message_type} for transformation {transformation_id}")
            else:
                print(f"Failed to send WebSocket notification: {response.status_code}")
    
    except Exception as e:
        # Don't fail the transformation if WebSocket notification fails
        print(f"Error sending WebSocket notification: {e}")


# Create async database session for tasks
async_engine = create_async_engine(
    settings.get_database_url(async_driver=True),
    echo=settings.DEBUG
)

AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


class TransformationTaskStatus:
    """Task status tracking"""
    PENDING = "pending"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"


def get_transformation_prompt(
    transformation_type: TransformationType, 
    document_content: str, 
    parameters: Dict[str, Any]
) -> str:
    """
    Generate a prompt for AI based on the transformation type
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


async def call_ai_provider(prompt: str, ai_provider: str = None) -> Dict[str, Any]:
    """
    Call the configured AI provider with fallback support
    """
    provider = ai_provider or settings.AI_PROVIDER
    
    try:
        if provider == "anthropic":
            return await call_claude_api(prompt)
        elif provider == "openai":
            return await call_openai_api(prompt)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    except Exception as e:
        # Try fallback provider if primary fails
        if provider == "anthropic" and settings.OPENAI_API_KEY:
            return await call_openai_api(prompt)
        elif provider == "openai" and settings.CLAUDE_API_KEY:
            return await call_claude_api(prompt)
        else:
            raise e


async def call_claude_api(prompt: str) -> Dict[str, Any]:
    """Call Anthropic Claude API"""
    if not settings.CLAUDE_API_KEY:
        raise ValueError("Claude API key not configured")
    
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=settings.AI_TEMPERATURE,
            system="You are an expert content repurposing assistant. Your task is to transform the provided content into the requested format while maintaining the key information and adapting the style appropriately.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "content": message.content[0].text,
            "provider": "claude",
            "model": "claude-3-sonnet-20240229",
            "tokens_used": message.usage.input_tokens + message.usage.output_tokens if hasattr(message, 'usage') else None
        }
    
    except Exception as e:
        raise Exception(f"Claude API error: {str(e)}")


async def call_openai_api(prompt: str) -> Dict[str, Any]:
    """Call OpenAI GPT API"""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = await client.chat.completions.create(
            model=settings.DEFAULT_AI_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert content repurposing assistant. Your task is to transform the provided content into the requested format while maintaining the key information and adapting the style appropriately."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=settings.AI_MAX_TOKENS,
            temperature=settings.AI_TEMPERATURE
        )
        
        return {
            "content": response.choices[0].message.content,
            "provider": "openai",
            "model": settings.DEFAULT_AI_MODEL,
            "tokens_used": response.usage.total_tokens if response.usage else None
        }
    
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.transformation_tasks.process_transformation")
def process_transformation_task(
    self,
    transformation_id: str,
    document_path: str,
    transformation_type: str,
    parameters: Dict[str, Any],
    workspace_id: str,
    user_id: str
):
    """
    Celery task to process AI transformation
    """
    # Convert string IDs back to UUIDs
    transformation_uuid = uuid.UUID(transformation_id)
    workspace_uuid = uuid.UUID(workspace_id)
    user_uuid = uuid.UUID(user_id)
    
    # Update task status to started
    self.update_state(
        state=TransformationTaskStatus.STARTED,
        meta={"progress": 0, "status": "Starting transformation..."}
    )
    
    # Run the async transformation in a new event loop
    return asyncio.run(
        _process_transformation_async(
            self,
            transformation_uuid,
            document_path,
            TransformationType(transformation_type),
            parameters,
            workspace_uuid,
            user_uuid
        )
    )


async def _process_transformation_async(
    task_instance,
    transformation_id: uuid.UUID,
    document_path: str,
    transformation_type: TransformationType,
    parameters: Dict[str, Any],
    workspace_id: uuid.UUID,
    user_id: uuid.UUID
):
    """
    Async implementation of transformation processing
    """
    async with AsyncSessionLocal() as db:
        try:
            # Update task progress
            task_instance.update_state(
                state=TransformationTaskStatus.PROGRESS,
                meta={"progress": 10, "status": "Loading transformation..."}
            )
            
            # Send WebSocket notification: transformation started
            await send_websocket_notification(
                workspace_id=str(workspace_id),
                user_id=str(user_id),
                transformation_id=str(transformation_id),
                message_type="transformation_started",
                data={"progress": 10, "status": "Loading transformation..."}
            )
            
            # Get transformation record
            await workspace_service.set_workspace_context(db, workspace_id)
            
            stmt = select(TransformationDB).where(TransformationDB.id == transformation_id)
            result = await db.execute(stmt)
            transformation = result.scalar_one_or_none()
            
            if not transformation:
                raise Exception("Transformation not found")
            
            # Update status to processing
            transformation.status = TransformationStatus.PROCESSING
            transformation.updated_at = datetime.utcnow()
            await db.commit()
            
            # Update task progress
            task_instance.update_state(
                state=TransformationTaskStatus.PROGRESS,
                meta={"progress": 20, "status": "Reading document content..."}
            )
            
            # Read document content
            try:
                with open(document_path, "r", encoding="utf-8") as file:
                    document_content = file.read()
            except Exception as e:
                raise Exception(f"Failed to read document: {str(e)}")
            
            # Update task progress
            task_instance.update_state(
                state=TransformationTaskStatus.PROGRESS,
                meta={"progress": 40, "status": "Generating AI prompt..."}
            )
            
            # Prepare the prompt
            prompt = get_transformation_prompt(transformation_type, document_content, parameters)
            
            # Update task progress
            task_instance.update_state(
                state=TransformationTaskStatus.PROGRESS,
                meta={"progress": 60, "status": "Calling AI provider..."}
            )
            
            # Send WebSocket notification: AI processing
            await send_websocket_notification(
                workspace_id=str(workspace_id),
                user_id=str(user_id),
                transformation_id=str(transformation_id),
                message_type="transformation_progress",
                data={"progress": 60, "status": "Calling AI provider..."}
            )
            
            # Call AI API
            ai_result = await call_ai_provider(prompt)
            
            # Update task progress
            task_instance.update_state(
                state=TransformationTaskStatus.PROGRESS,
                meta={"progress": 80, "status": "Saving results..."}
            )
            
            # Update transformation with result
            transformation.result = ai_result["content"]
            transformation.status = TransformationStatus.COMPLETED
            transformation.updated_at = datetime.utcnow()
            transformation.ai_provider = ai_result["provider"]
            transformation.ai_model = ai_result["model"]
            transformation.tokens_used = ai_result.get("tokens_used")
            
            await db.commit()
            
            # Update task progress to completed
            task_instance.update_state(
                state=TransformationTaskStatus.SUCCESS,
                meta={"progress": 100, "status": "Transformation completed successfully!"}
            )
            
            # Send WebSocket notification: transformation completed
            await send_websocket_notification(
                workspace_id=str(workspace_id),
                user_id=str(user_id),
                transformation_id=str(transformation_id),
                message_type="transformation_completed",
                data={
                    "progress": 100,
                    "status": "Transformation completed successfully!",
                    "result_preview": ai_result["content"][:200] + "..." if len(ai_result["content"]) > 200 else ai_result["content"],
                    "provider": ai_result["provider"],
                    "tokens_used": ai_result.get("tokens_used")
                }
            )
            
            return {
                "transformation_id": str(transformation_id),
                "status": "completed",
                "result": ai_result["content"][:100] + "..." if len(ai_result["content"]) > 100 else ai_result["content"],
                "provider": ai_result["provider"],
                "tokens_used": ai_result.get("tokens_used")
            }
        
        except Exception as e:
            # Update transformation with error
            if 'transformation' in locals():
                transformation.status = TransformationStatus.FAILED
                transformation.error_message = f"Error processing transformation: {str(e)}"
                transformation.updated_at = datetime.utcnow()
                await db.commit()
            
            # Update task status to failure
            task_instance.update_state(
                state=TransformationTaskStatus.FAILURE,
                meta={"progress": 0, "status": f"Transformation failed: {str(e)}"}
            )
            
            # Send WebSocket failure notification
            await send_websocket_notification(
                workspace_id=str(workspace_id),
                user_id=str(user_id),
                transformation_id=str(transformation_id),
                message_type="transformation_failed",
                data={"error_message": str(e)}
            )
            
            # Re-raise for Celery retry mechanism
            raise task_instance.retry(exc=e, countdown=60, max_retries=3)
        
        finally:
            await workspace_service.clear_workspace_context(db)


@celery_app.task(name="app.tasks.transformation_tasks.get_task_status")
def get_task_status(task_id: str):
    """
    Get the status of a transformation task
    """
    result = celery_app.AsyncResult(task_id)
    
    if result.state == 'PENDING':
        return {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": "Task is waiting to be processed..."
        }
    elif result.state == TransformationTaskStatus.STARTED:
        return {
            "task_id": task_id,
            "status": "started",
            "progress": result.info.get("progress", 0),
            "message": result.info.get("status", "Task started...")
        }
    elif result.state == TransformationTaskStatus.PROGRESS:
        return {
            "task_id": task_id,
            "status": "progress",
            "progress": result.info.get("progress", 0),
            "message": result.info.get("status", "Processing...")
        }
    elif result.state == TransformationTaskStatus.SUCCESS:
        return {
            "task_id": task_id,
            "status": "success",
            "progress": 100,
            "message": "Task completed successfully!",
            "result": result.result
        }
    elif result.state == TransformationTaskStatus.FAILURE:
        return {
            "task_id": task_id,
            "status": "failed",
            "progress": 0,
            "message": f"Task failed: {str(result.info)}",
            "error": str(result.info)
        }
    else:
        return {
            "task_id": task_id,
            "status": result.state.lower(),
            "progress": 0,
            "message": f"Unknown task state: {result.state}"
        }


@celery_app.task(name="app.tasks.transformation_tasks.cancel_task")
def cancel_task(task_id: str):
    """
    Cancel a running transformation task
    """
    celery_app.control.revoke(task_id, terminate=True)
    return {"task_id": task_id, "status": "cancelled"}