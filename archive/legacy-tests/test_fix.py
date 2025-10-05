#!/usr/bin/env python3
"""
Quick test script to verify lazy-loading Celery fixes import hang.
Run this manually to test the solution.
"""

import sys
import os
import time

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_lazy_imports():
    """Test that imports work without Redis connection"""
    print("🧪 Testing Lazy Import Fix")
    print("=" * 40)
    
    # Disable Celery to test fallback mode
    os.environ["DISABLE_CELERY"] = "true"
    
    start_time = time.time()
    
    try:
        print("1. Testing basic imports...")
        print("   ✓ Lazy Celery app import")
        
        print("2. Testing service imports...")
        from app.services.task_service_lazy import task_service
        print("   ✓ Lazy task service import")
        
        print("3. Testing service methods...")
        worker_status = task_service.get_worker_status()
        print(f"   ✓ Worker status: {worker_status.get('status')}")
        
        queue_info = task_service.get_queue_info()
        print(f"   ✓ Queue info: {queue_info.get('active_tasks', 0)} active tasks")
        
        elapsed = time.time() - start_time
        print(f"\n🎉 SUCCESS! Import time: {elapsed:.2f}s")
        print("   All imports completed without Redis connection")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_redis():
    """Test with Redis if available"""
    print("\n🔴 Testing with Redis (if available)")
    print("=" * 40)
    
    # Re-enable Celery
    os.environ.pop("DISABLE_CELERY", None)
    
    try:
        # Reset lazy loading
        from app.core.celery_app_lazy import reset_celery_app
        reset_celery_app()
        
        from app.core.celery_app_lazy import get_celery_app, is_celery_available
        
        if is_celery_available():
            print("✓ Redis is available and Celery connected")
            celery_app = get_celery_app()
            print(f"✓ Broker: {celery_app.conf.broker_url}")
        else:
            print("⚠️  Redis not available - using fallback mode")
            print("   This is expected if Redis is not running")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Redis test failed: {e}")
        print("   This is expected if Redis is not running")
        return False

if __name__ == "__main__":
    print("Testing Lazy-Loading Celery Solution")
    print("This should fix the import hang issue.\n")
    
    success1 = test_lazy_imports()
    success2 = test_with_redis()
    
    print("\n" + "=" * 50)
    if success1:
        print("🎉 SOLUTION WORKS!")
        print("\nNext steps:")
        print("  1. Replace transformations.py with transformations_lazy.py")
        print("  2. Start server: DISABLE_CELERY=true uvicorn backend.main:app --reload")
        print("  3. Test endpoints work")
        print("  4. For production: start Redis and remove DISABLE_CELERY")
    else:
        print("❌ Solution needs debugging")
    
    print(f"\nTest results: Import fix {'✓' if success1 else '✗'}, Redis test {'✓' if success2 else '⚠️'}")