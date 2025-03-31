from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic
import os

from app.models.transformations import (
    Transformation, TransformationCreate, TransformationList,
    TransformationType, TransformationStatus
)
from app.api.routes.auth import get_current_user
from app.api.routes.documents import DOCUMENTS_DB
from app.core.config import settings

# Mock database for transformations - in a real app, use a proper database
TRANSFORMATIONS_DB = []
transformation_id_counter = 1

router = APIRouter()

def get_document_by_id(document_id: int, user_id: int):
    for doc in DOCUMENTS_DB:
        if doc["id"] == document_id and doc["user_id"] == user_id:
            return doc
    return None

async def process_transformation(transformation_id: int, document_path: str, transformation_type: TransformationType, parameters: Dict[str, Any]):
    """
    Background task to process the transformation using Claude API
    """
    # Get the transformation from the database
    transformation = None
    for t in TRANSFORMATIONS_DB:
        if t["id"] == transformation_id:
            transformation = t
            break
    
    if not transformation:
        return
    
    # Update status to processing
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
        transformation["result"] = message.content[0].text
        transformation["status"] = TransformationStatus.COMPLETED
        transformation["updated_at"] = datetime.now()
        
    except Exception as e:
        # Update transformation with error
        transformation["status"] = TransformationStatus.FAILED
        transformation["result"] = f"Error processing transformation: {str(e)}"
        transformation["updated_at"] = datetime.now()

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
    current_user: dict = Depends(get_current_user)
):
    global transformation_id_counter
    
    # Validate document exists and belongs to user
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
async def get_user_transformations(current_user: dict = Depends(get_current_user)):
    user_transformations = [t for t in TRANSFORMATIONS_DB if t["user_id"] == current_user["id"]]
    return {"transformations": user_transformations, "count": len(user_transformations)}

@router.get("/transformations/{transformation_id}", response_model=Transformation)
async def get_transformation(transformation_id: int, current_user: dict = Depends(get_current_user)):
    for transformation in TRANSFORMATIONS_DB:
        if transformation["id"] == transformation_id and transformation["user_id"] == current_user["id"]:
            return transformation
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Transformation not found"
    )

@router.delete("/transformations/{transformation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transformation(transformation_id: int, current_user: dict = Depends(get_current_user)):
    for i, transformation in enumerate(TRANSFORMATIONS_DB):
        if transformation["id"] == transformation_id and transformation["user_id"] == current_user["id"]:
            TRANSFORMATIONS_DB.pop(i)
            return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Transformation not found"
    )