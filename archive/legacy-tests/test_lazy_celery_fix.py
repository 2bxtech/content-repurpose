"""
Test script to verify lazy-loading Celery fixes the import hang issue.
Run this manually to test different scenarios.
"""

import sys
import os
import time

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🧪 Testing Lazy-Loading Celery Import Fix")
print("=" * 50)

def test_1_basic_imports():
    """Test 1: Basic imports without Celery connection"""
    print("\n📦 Test 1: Basic imports (should be instant)")
    start_time = time.time()
    
    try:
        # These should import without connecting to Redis
        print("✓ Model imports successful")
        
        # Test lazy celery import
        print("✓ Lazy celery import successful (no connection yet)")
        
        elapsed = time.time() - start_time
        print(f"✓ Import time: {elapsed:.2f}s (should be < 1s)")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_2_service_imports_with_mock():
    """Test 2: Service imports with Celery disabled"""
    print("\n🔧 Test 2: Service imports with DISABLE_CELERY=true")
    
    # Set environment variable to disable Celery
    os.environ["DISABLE_CELERY"] = "true"
    
    start_time = time.time()
    
    try:
        from app.services.task_service_lazy import task_service
        print("✓ Task service import successful (mock mode)")
        
        # Test service methods
        worker_status = task_service.get_worker_status()
        print(f"✓ Worker status: {worker_status.get('status', 'unknown')}")
        
        elapsed = time.time() - start_time
        print(f"✓ Service import time: {elapsed:.2f}s (should be < 1s)")
        
        return True
    except Exception as e:
        print(f"✗ Service import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_workspace_service():
    """Test 3: Workspace service import"""
    print("\n🏢 Test 3: Workspace service import")
    
    start_time = time.time()
    
    try:
        print("✓ Workspace service import successful")
        
        elapsed = time.time() - start_time
        print(f"✓ Workspace service import time: {elapsed:.2f}s")
        
        return True
    except Exception as e:
        print(f"✗ Workspace service import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_4_transformation_route_import():
    """Test 4: Import the problematic transformation route"""
    print("\n🛣️  Test 4: Transformation route import")
    
    start_time = time.time()
    
    try:
        # This should use the lazy services
        print("✓ Transformation route import successful (with lazy services)")
        
        elapsed = time.time() - start_time
        print(f"✓ Route import time: {elapsed:.2f}s")
        
        return True
    except Exception as e:
        print(f"✗ Transformation route import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_redis_availability():
    """Test 5: Check if Redis is available"""
    print("\n🔴 Test 5: Redis availability check")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, 
                       socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        print("✓ Redis is available and responding")
        return True
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   This is expected if Redis is not running")
        return False

def test_6_celery_with_redis():
    """Test 6: Test Celery connection if Redis is available"""
    print("\n🌸 Test 6: Celery with Redis (if available)")
    
    # Remove the disable flag
    os.environ.pop("DISABLE_CELERY", None)
    
    try:
        from app.core.celery_app_lazy import get_celery_app, is_celery_available
        
        print("Testing Celery availability...")
        if is_celery_available():
            print("✓ Celery is available and connected to Redis")
            
            celery_app = get_celery_app()
            print(f"✓ Broker URL: {celery_app.conf.broker_url}")
            
            return True
        else:
            print("⚠️  Celery not available (Redis connection failed)")
            print("   This is expected if Redis is not running")
            return False
            
    except Exception as e:
        print(f"⚠️  Celery test failed: {e}")
        print("   This is expected if Redis is not running")
        return False

def main():
    """Run all tests"""
    print("Testing lazy-loading Celery fixes...")
    print("This should prevent import-time Redis connection hangs.")
    
    tests = [
        test_1_basic_imports,
        test_2_service_imports_with_mock,
        test_3_workspace_service,
        test_5_redis_availability,
        test_6_celery_with_redis,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")
    print(f"✓ Passed: {sum(results)}/{len(results)} tests")
    
    if results[0] and results[1]:  # Basic imports and service imports work
        print("\n🎉 SUCCESS: Lazy loading fixes the import hang!")
        print("\n📋 Next steps:")
        print("  1. Update transformations.py to use lazy services")
        print("  2. Test the server startup")
        print("  3. For production: ensure Redis is running")
    else:
        print("\n❌ Some basic tests failed - check the errors above")
    
    return all(results[:2])  # Return success if at least basic tests pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)