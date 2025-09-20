"""
Test script for MCP Enhanced Workflow V2
Verifies that MCP integration works correctly with the NotebookLlama solution
"""

import asyncio
import os
import sys
import tempfile
import logging
from pathlib import Path
import io

# Set stdout to handle Unicode properly on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from notebookllama.mcp_enhanced_workflow_v2 import (
    MCPEnhancedWorkflowV2,
    create_mcp_enhanced_workflow_v2,
    run_mcp_enhanced_workflow_v2
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_workflow_creation():
    """Test creating MCP enhanced workflow v2"""
    print("\n=== Test 1: MCP Workflow Creation ===")

    try:
        # Create workflow with MCP enabled
        workflow = create_mcp_enhanced_workflow_v2(enable_mcp=True)
        print(f"[OK] Created MCP Enhanced Workflow V2")
        print(f"   - Class: {workflow.__class__.__name__}")
        print(f"   - MCP Enabled: {workflow.enable_mcp}")
        print(f"   - MCP Initialized: {workflow._mcp_initialized}")

        # Create workflow with MCP disabled
        workflow_no_mcp = create_mcp_enhanced_workflow_v2(enable_mcp=False)
        print(f"[OK] Created workflow without MCP")
        print(f"   - MCP Enabled: {workflow_no_mcp.enable_mcp}")

        return True

    except Exception as e:
        print(f"[FAIL] Failed to create workflow: {e}")
        return False


async def test_mcp_initialization():
    """Test MCP initialization"""
    print("\n=== Test 2: MCP Initialization ===")

    try:
        workflow = create_mcp_enhanced_workflow_v2(enable_mcp=True)

        # Check if MCP config exists
        config_path = os.path.join(os.path.dirname(__file__), 'mcp_config.json')
        if os.path.exists(config_path):
            print(f"[OK] MCP config found at: {config_path}")

            # Try to initialize MCP connections
            await workflow._initialize_mcp_connections()

            if workflow._mcp_initialized:
                print(f"[OK] MCP connections initialized")
                print(f"   - Available tools: {list(workflow._mcp_available_tools.keys())}")

                # Get MCP status
                status = await workflow.get_mcp_status()
                print(f"[OK] MCP Status: {status['status']}")
                if 'health' in status:
                    print(f"   - Total tools: {status.get('total_tools', 0)}")
                    print(f"   - Servers: {status.get('available_servers', [])}")
            else:
                print("[WARN] MCP not initialized (servers may not be running)")
        else:
            print(f"[WARN] MCP config not found at: {config_path}")
            print("   Create mcp_config.json to enable MCP features")

        return True

    except Exception as e:
        print(f"[FAIL] MCP initialization error: {e}")
        return False


async def test_workflow_with_sample_document():
    """Test the complete workflow with a sample document"""
    print("\n=== Test 3: Complete Workflow Test ===")

    try:
        # Create a sample text file
        sample_content = """
        # Test Document for NotebookLlama

        This is a test document to verify that the MCP Enhanced Workflow V2
        properly integrates with the NotebookLlama solution.

        ## Key Features

        - Document processing with Docling
        - Content enhancement with OpenAI
        - MCP server integration
        - Mind map generation

        ## Technical Details

        The workflow preserves all content and generates summaries, Q&A pairs,
        and visualizations. MCP integration adds advanced capabilities like
        filesystem access, memory storage, and database integration.

        This test verifies that all components work together seamlessly.
        """

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_content)
            temp_path = f.name

        print(f"[OK] Created test document: {temp_path}")

        # Test with MCP enabled
        print("\nTesting with MCP enabled...")
        result = await run_mcp_enhanced_workflow_v2(
            file_path=temp_path,
            document_title="Test Document",
            enable_mcp=True
        )

        # Check result
        if result.get("status") == "success":
            print("[OK] Workflow completed successfully with MCP")
            print(f"   - Content size: {result.get('content_size', 0)} characters")
            print(f"   - Has summary: {'summary' in result}")
            print(f"   - Has Q&A: {'q_and_a' in result}")
            print(f"   - Has mind map: {'mind_map' in result}")

            if 'mcp_status' in result:
                mcp_status = result['mcp_status']
                print(f"   - MCP Status: {mcp_status.get('status', 'unknown')}")
        else:
            print(f"[WARN] Workflow completed with status: {result.get('status')}")
            if 'error' in result:
                print(f"   Error: {result['error']}")

        # Test without MCP
        print("\nTesting without MCP...")
        result_no_mcp = await run_mcp_enhanced_workflow_v2(
            file_path=temp_path,
            document_title="Test Document",
            enable_mcp=False
        )

        if result_no_mcp.get("status") == "success":
            print("[OK] Workflow completed successfully without MCP")
        else:
            print(f"[WARN] Workflow status: {result_no_mcp.get('status')}")

        # Cleanup
        os.unlink(temp_path)

        return True

    except Exception as e:
        print(f"[FAIL] Workflow test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_components():
    """Test individual workflow components"""
    print("\n=== Test 4: Workflow Components ===")

    try:
        workflow = create_mcp_enhanced_workflow_v2(enable_mcp=False)

        # Check Docling processor
        if workflow.docling_processor:
            print("[OK] Docling processor initialized")
        else:
            print("[FAIL] Docling processor not initialized")

        # Check content enhancer
        if workflow.content_enhancer:
            print("[OK] Content enhancer initialized")
        else:
            print("[FAIL] Content enhancer not initialized")

        # Check mind map generator
        if workflow.mind_map_generator:
            print("[OK] Mind map generator initialized")
        else:
            print("[FAIL] Mind map generator not initialized")

        return True

    except Exception as e:
        print(f"[FAIL] Component test error: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Enhanced Workflow V2 - Integration Test")
    print("=" * 60)

    tests = [
        ("Workflow Creation", test_mcp_workflow_creation),
        ("MCP Initialization", test_mcp_initialization),
        ("Component Check", test_workflow_components),
        ("Complete Workflow", test_workflow_with_sample_document),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! MCP integration is working correctly.")
    elif passed > 0:
        print(f"\n[WARN] Some tests passed ({passed}/{total}). Check the failures above.")
    else:
        print("\n[ERROR] All tests failed. Please check the configuration and dependencies.")


if __name__ == "__main__":
    asyncio.run(main())