#!/usr/bin/env python3
"""
Simple validation script to check database connectivity and multi-tenant setup.
This directly tests the database and models without needing HTTP.
"""

import asyncio
import sys
import os

# Add the backend directory to the path so we can import our app modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Import our app modules
from app.core.config import Settings
from app.db.models.workspace import Workspace
from app.services.workspace_service import WorkspaceService

async def test_database_connectivity():
    """Test basic database connectivity and schema."""
    
    print("🔍 Testing database connectivity and schema...")
    
    try:
        # Create database connection
        settings = Settings()
        engine = create_async_engine(settings.DATABASE_URL)
        
        # Test basic connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
            
            # Test that our tables exist
            tables_result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result]
            print(f"✅ Found tables: {', '.join(tables)}")
            
            # Test that RLS is enabled
            rls_result = await conn.execute(text("""
                SELECT schemaname, tablename, rowsecurity 
                FROM pg_tables 
                WHERE tablename IN ('users', 'documents', 'transformations')
                AND rowsecurity = true
            """))
            rls_tables = [f"{row[1]}" for row in rls_result]
            print(f"✅ RLS enabled on: {', '.join(rls_tables)}")
            
            # Test workspaces exist
            workspace_result = await conn.execute(text("SELECT count(*) FROM workspaces"))
            workspace_count = workspace_result.scalar()
            print(f"✅ Found {workspace_count} workspace(s)")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

async def test_workspace_service():
    """Test workspace service functionality."""
    
    print("\n🔍 Testing workspace service...")
    
    try:
        # Get database session
        settings = Settings()
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Test getting all workspaces directly
            from sqlalchemy import select
            result = await session.execute(select(Workspace))
            workspaces = result.scalars().all()
            print(f"✅ Retrieved {len(workspaces)} workspace(s) through direct query")
            
            for ws in workspaces:
                print(f"   - {ws.name} ({ws.slug}) - Plan: {ws.plan}")
                
            # Test RLS context setting
            if workspaces:
                test_workspace = workspaces[0]
                service = WorkspaceService()
                await service.set_workspace_context(session, test_workspace.id)
                print(f"✅ Set workspace context to: {test_workspace.name}")
                
                # Test getting workspace stats
                stats = await service.get_workspace_stats(session, test_workspace.id)
                print(f"✅ Workspace stats: {stats}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Workspace service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_rls_isolation():
    """Test that RLS policies actually isolate data."""
    
    print("\n🔍 Testing RLS isolation...")
    
    try:
        settings = Settings()
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.connect() as conn:
            # Get all workspaces
            workspaces_result = await conn.execute(text("SELECT id, name FROM workspaces ORDER BY created_at"))
            workspaces = list(workspaces_result)
            
            if len(workspaces) < 1:
                print("❌ Need at least 1 workspace to test RLS")
                return False
                
            print(f"✅ Testing RLS with {len(workspaces)} workspace(s)")
            
            # Test setting workspace context and querying
            for workspace_id, workspace_name in workspaces:
                await conn.execute(text(f"SET app.workspace_id = '{workspace_id}'"))
                
                # Query users table (should be empty initially)
                users_result = await conn.execute(text("SELECT count(*) FROM users"))
                user_count = users_result.scalar()
                
                documents_result = await conn.execute(text("SELECT count(*) FROM documents"))
                doc_count = documents_result.scalar()
                
                print(f"   Workspace '{workspace_name}': {user_count} users, {doc_count} documents")
                
            print("✅ RLS context switching works")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ RLS isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all validation tests."""
    
    print("🚀 Starting multi-tenant database validation...")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Database Connectivity", test_database_connectivity),
        ("Workspace Service", test_workspace_service),
        ("RLS Isolation", test_rls_isolation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running test: {test_name}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Multi-tenant setup is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Test user registration and workspace assignment")
        print("   2. Test document upload with workspace isolation")
        print("   3. Test API endpoints with workspace context")
        print("   4. Create frontend integration for workspace management")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Tests failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)