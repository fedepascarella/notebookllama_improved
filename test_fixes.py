#!/usr/bin/env python3
"""
Test script to validate the comprehensive fixes for NotebookLLaMA Enhanced
"""

import os
import sys
import asyncio
import traceback
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        # Test core modules
        from notebookllama.postgres_manager import DOCUMENT_MANAGER
        print("✅ PostgreSQL manager imported")
        
        from notebookllama.enhanced_querying import EnhancedQueryEngine
        print("✅ Enhanced querying imported")
        
        from notebookllama.enhanced_workflow import WF
        print("✅ Enhanced workflow imported")
        
        # Test Docling
        from docling.document_converter import DocumentConverter
        print("✅ Docling imported")
        
        # Test async support
        import nest_asyncio
        print("✅ nest-asyncio imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_database_connection():
    """Test database connectivity"""
    print("\n🧪 Testing database connection...")
    
    try:
        from notebookllama.postgres_manager import DOCUMENT_MANAGER
        
        # Test basic database connection
        session = DOCUMENT_MANAGER.get_session()
        session.close()
        print("✅ Database connection successful")
        
        # Test vector store initialization status
        if DOCUMENT_MANAGER.vector_store:
            print("✅ Vector store initialized")
        else:
            print("⚠️ Vector store not initialized (may need OpenAI API key)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def test_query_engine():
    """Test the enhanced query engine"""
    print("\n🧪 Testing query engine...")
    
    try:
        from notebookllama.enhanced_querying import EnhancedQueryEngine
        
        # Create query engine
        query_engine = EnhancedQueryEngine()
        print("✅ Query engine created")
        
        # Test query with no documents (should handle gracefully)
        response = await query_engine.query_index("What is this document about?")
        
        if response is None:
            print("✅ Query engine handled empty database correctly")
        else:
            print(f"✅ Query engine returned response: {len(response)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Query engine error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

async def test_workflow():
    """Test the enhanced workflow"""
    print("\n🧪 Testing workflow...")
    
    try:
        from notebookllama.enhanced_workflow import WF, FileInputEvent
        from llama_index.core.workflow.events import StartEvent
        
        # Create workflow
        workflow = WF()
        print("✅ Workflow created")
        
        # Create test start event
        start_event = StartEvent()
        start_event.file_path = "test.txt"
        start_event.content = "This is a test document for the workflow."
        start_event.file_type = "txt"
        
        # Test workflow execution
        result = await workflow.run(start_event=start_event)
        
        if isinstance(result, dict) and "status" in result:
            print(f"✅ Workflow executed: {result.get('status')}")
        else:
            print("✅ Workflow executed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_system_status():
    """Test overall system status"""
    print("\n🧪 Testing system status...")
    
    status = {
        "docling": False,
        "postgres": False,
        "openai": False,
        "vector_store": False
    }
    
    # Test Docling
    try:
        from docling.document_converter import DocumentConverter
        status["docling"] = True
        print("✅ Docling ready")
    except Exception:
        print("❌ Docling not available")
    
    # Test PostgreSQL
    try:
        from notebookllama.postgres_manager import DOCUMENT_MANAGER
        session = DOCUMENT_MANAGER.get_session()
        session.close()
        status["postgres"] = True
        print("✅ PostgreSQL connected")
    except Exception:
        print("❌ PostgreSQL not connected")
    
    # Test OpenAI
    if os.getenv("OPENAI_API_KEY"):
        status["openai"] = True
        print("✅ OpenAI configured")
    else:
        print("⚠️ OpenAI API key not set")
    
    # Test Vector Store
    try:
        from notebookllama.postgres_manager import DOCUMENT_MANAGER
        if DOCUMENT_MANAGER.vector_store:
            status["vector_store"] = True
            print("✅ Vector store ready")
        else:
            print("⚠️ Vector store not initialized")
    except Exception:
        print("❌ Vector store error")
    
    return status

async def main():
    """Run all tests"""
    print("🚀 Starting NotebookLLaMA Enhanced Fix Validation\n")
    
    results = {
        "imports": test_imports(),
        "database": test_database_connection(),
        "query_engine": await test_query_engine(),
        "workflow": await test_workflow(),
    }
    
    system_status = test_system_status()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper():<15} {status}")
    
    print("\n📋 SYSTEM STATUS:")
    for component, status in system_status.items():
        status_str = "✅ Ready" if status else "❌ Not Ready"
        print(f"{component.upper():<15} {status_str}")
    
    print("\n🎯 RECOMMENDATIONS:")
    
    if not system_status["openai"]:
        print("- Set OPENAI_API_KEY environment variable for full functionality")
    
    if not system_status["postgres"]:
        print("- Start PostgreSQL service: docker-compose up -d")
    
    if not system_status["vector_store"]:
        print("- Vector search may not work without OpenAI API key")
    
    # Overall assessment
    critical_tests = ["imports", "database", "query_engine"]
    critical_passed = all(results[test] for test in critical_tests)
    
    if critical_passed:
        print("\n🎉 CRITICAL FIXES VALIDATED SUCCESSFULLY!")
        print("   The chat interface should now work properly.")
    else:
        print("\n⚠️ Some critical tests failed. Please check the errors above.")
    
    return critical_passed

if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        sys.exit(1)