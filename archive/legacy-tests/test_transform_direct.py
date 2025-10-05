# test_transform_direct.py
import asyncio
from app.api.routes.transformations import create_transformation
from app.api.routes.transformations import TransformationRequest, TransformationParameters

async def test_transformation():
    # Test your logic directly
    request = TransformationRequest(
        sourceDocument="test content",
        transformationType="summary", 
        parameters=TransformationParameters(wordCount=100, tone="professional")
    )
    
    try:
        result = await create_transformation(request)
        print("✅ Transformation successful:")
        print(result)
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_transformation())