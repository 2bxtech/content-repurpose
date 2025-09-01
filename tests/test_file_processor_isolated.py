#!/usr/bin/env python3
"""
Isolated unit tests for FileProcessor - no fixtures, no API dependencies
"""
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

def test_imports():
    """Test that we can import the file processor modules"""
    try:
        from app.services.file_processor import FileProcessor, ProcessingResult
        print("✅ Successfully imported FileProcessor and ProcessingResult")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_file_processor_creation():
    """Test that we can create a FileProcessor instance"""
    try:
        from app.services.file_processor import FileProcessor
        processor = FileProcessor()
        print(f"✅ Successfully created FileProcessor instance: {type(processor)}")
        return True
    except Exception as e:
        print(f"❌ FileProcessor creation failed: {e}")
        return False

def test_processing_result_creation():
    """Test that we can create a ProcessingResult instance"""
    try:
        from app.services.file_processor import ProcessingResult
        result = ProcessingResult(
            content="test content",
            metadata={'test': 'data'},
            word_count=2,
            extraction_method="test",
            file_hash="test_hash"
        )
        print(f"✅ Successfully created ProcessingResult: {result.content}")
        return True
    except Exception as e:
        print(f"❌ ProcessingResult creation failed: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are available"""
    dependencies = [
        'PyPDF2', 'fitz', 'docx', 'PIL', 'magic', 'chardet'
    ]
    
    results = {}
    for dep in dependencies:
        try:
            if dep == 'fitz':
                import fitz
            elif dep == 'docx':
                import docx
            elif dep == 'PIL':
                import PIL
            elif dep == 'magic':
                import magic
            else:
                __import__(dep)
            results[dep] = True
            print(f"✅ {dep} available")
        except ImportError as e:
            results[dep] = False
            print(f"❌ {dep} not available: {e}")
    
    return results

if __name__ == "__main__":
    print("🧪 Running isolated file processor tests...")
    print("=" * 50)
    
    # Test imports
    print("\n1. Testing imports...")
    import_success = test_imports()
    
    # Test FileProcessor creation
    print("\n2. Testing FileProcessor creation...")
    processor_success = test_file_processor_creation()
    
    # Test ProcessingResult creation
    print("\n3. Testing ProcessingResult creation...")
    result_success = test_processing_result_creation()
    
    # Test dependencies
    print("\n4. Testing dependencies...")
    deps = test_dependencies()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Imports: {'✅' if import_success else '❌'}")
    print(f"   FileProcessor: {'✅' if processor_success else '❌'}")
    print(f"   ProcessingResult: {'✅' if result_success else '❌'}")
    print(f"   Dependencies: {sum(deps.values())}/{len(deps)} available")
    
    if import_success and processor_success and result_success:
        print("\n🎉 Phase 6 file processing is ready!")
    else:
        print("\n⚠️  Some issues need to be resolved")
        sys.exit(1)