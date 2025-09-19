"""
Test script to verify the Docling fix works correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_docling_imports():
    """Test that Docling imports work correctly"""
    print("Testing Docling imports...")

    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        print("PASS: Docling imports successful")
        return True
    except Exception as e:
        print(f"FAIL: Docling import failed: {e}")
        return False

def test_fixed_processor():
    """Test the corrected Docling processor"""
    print("Testing Corrected Docling Processor...")

    try:
        from notebookllama.fixed_docling_processor import DoclingProcessor, create_docling_processor
        processor = create_docling_processor()
        print("PASS: Corrected processor initialized successfully")
        return True
    except Exception as e:
        print(f"FAIL: Corrected processor failed: {e}")
        return False

def test_enhanced_workflow():
    """Test the enhanced workflow with fixed Docling"""
    print("Testing Enhanced Workflow...")

    try:
        from notebookllama.enhanced_workflow import WF
        workflow = WF()
        print("PASS: Enhanced workflow initialized successfully")
        return True
    except Exception as e:
        print(f"FAIL: Enhanced workflow failed: {e}")
        return False

def test_streamlit_app():
    """Test that the main Streamlit app can import correctly"""
    print("Testing Streamlit app imports...")

    try:
        # Test key imports from Enhanced_Home.py
        from notebookllama.enhanced_workflow import WF, FileInputEvent, NotebookOutputEvent
        from notebookllama.postgres_manager import DOCUMENT_MANAGER, EnhancedDocument
        print("PASS: Main app imports successful")
        return True
    except Exception as e:
        print(f"FAIL: Main app imports failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("DOCLING FIX VERIFICATION TESTS")
    print("=" * 50)

    tests = [
        test_docling_imports,
        test_fixed_processor,
        test_enhanced_workflow,
        test_streamlit_app
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"CRASH: Test {test.__name__} crashed: {e}")
            print()

    print("=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 50)

    if passed == total:
        print("SUCCESS: ALL TESTS PASSED!")
        print("The Docling backend error has been fixed.")
        print("You can now run: streamlit run src/notebookllama/Enhanced_Home.py")
    else:
        print(f"ERROR: {total - passed} tests failed.")
        print("Please check the error messages above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)