"""
Streamlit Async Handler - Senior-level async integration for Streamlit
Solves "Task was destroyed but it is pending!" errors and session state issues
Based on 2024 best practices for Streamlit async handling
"""

import asyncio
import logging
import threading
import concurrent.futures
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime
import streamlit as st
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class StreamlitAsyncHandler:
    """
    Senior-level async handler for Streamlit applications.
    Implements task scheduling pattern recommended for production use in 2024.

    Features:
    - Proper event loop management
    - Task cleanup to prevent "pending task" errors
    - Session state preservation
    - Error handling and recovery
    - Progress tracking for long-running tasks
    """

    def __init__(self):
        self.active_tasks = set()
        self._executor = None
        self._init_executor()

    def _init_executor(self):
        """Initialize thread pool executor for async tasks"""
        try:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=2,  # Limit concurrent tasks
                thread_name_prefix="streamlit_async"
            )
            logger.info("Async executor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize executor: {e}")
            raise

    def run_async_task(
        self,
        coro: Awaitable[Any],
        task_name: str = "async_task",
        timeout: int = 300,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Any:
        """
        Run async coroutine in Streamlit-compatible way

        Args:
            coro: Async coroutine to run
            task_name: Name for logging and tracking
            timeout: Timeout in seconds
            progress_callback: Optional callback for progress updates

        Returns:
            Result of the coroutine

        Raises:
            TimeoutError: If task times out
            Exception: If task fails
        """
        logger.info(f"Starting async task: {task_name}")

        try:
            # Method 1: Try with existing event loop (task scheduling)
            try:
                loop = asyncio.get_running_loop()
                logger.debug("Using existing event loop with task scheduling")
                return self._run_with_task_scheduling(coro, loop, timeout, progress_callback)

            except RuntimeError:
                # Method 2: No running loop - use thread executor
                logger.debug("No running loop, using thread executor")
                return self._run_with_thread_executor(coro, timeout, progress_callback)

        except Exception as e:
            logger.error(f"Async task '{task_name}' failed: {e}")
            logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

        finally:
            # Cleanup
            self._cleanup_completed_tasks()

    def _run_with_task_scheduling(
        self,
        coro: Awaitable[Any],
        loop: asyncio.AbstractEventLoop,
        timeout: int,
        progress_callback: Optional[Callable[[str], None]]
    ) -> Any:
        """
        Run coroutine using task scheduling (2024 best practice)
        """
        # Create task with proper tracking
        task = loop.create_task(self._wrap_coroutine(coro, progress_callback))
        self.active_tasks.add(task)

        try:
            # Use run_until_complete with timeout
            future = asyncio.wait_for(task, timeout=timeout)
            result = loop.run_until_complete(future)
            return result

        except asyncio.TimeoutError:
            # Cancel task properly to prevent pending error
            task.cancel()
            try:
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                pass
            raise TimeoutError(f"Task timed out after {timeout} seconds")

        finally:
            # Remove from tracking
            self.active_tasks.discard(task)

    def _run_with_thread_executor(
        self,
        coro: Awaitable[Any],
        timeout: int,
        progress_callback: Optional[Callable[[str], None]]
    ) -> Any:
        """
        Run coroutine in separate thread with new event loop
        """
        def run_in_thread():
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run coroutine with timeout
                wrapped_coro = self._wrap_coroutine(coro, progress_callback)
                return loop.run_until_complete(
                    asyncio.wait_for(wrapped_coro, timeout=timeout)
                )
            finally:
                # Proper cleanup
                try:
                    # Cancel all remaining tasks
                    pending_tasks = asyncio.all_tasks(loop)
                    for task in pending_tasks:
                        task.cancel()

                    # Wait for cancellations to complete
                    if pending_tasks:
                        loop.run_until_complete(
                            asyncio.gather(*pending_tasks, return_exceptions=True)
                        )
                finally:
                    loop.close()

        # Submit to thread executor
        future = self._executor.submit(run_in_thread)
        return future.result(timeout=timeout + 10)  # Extra time for cleanup

    async def _wrap_coroutine(
        self,
        coro: Awaitable[Any],
        progress_callback: Optional[Callable[[str], None]]
    ) -> Any:
        """
        Wrap coroutine with progress tracking and error handling
        """
        if progress_callback:
            progress_callback("Starting task...")

        try:
            result = await coro

            if progress_callback:
                progress_callback("Task completed successfully")

            return result

        except asyncio.CancelledError:
            if progress_callback:
                progress_callback("Task was cancelled")
            raise

        except Exception as e:
            if progress_callback:
                progress_callback(f"Task failed: {str(e)}")
            raise

    def _cleanup_completed_tasks(self):
        """Clean up completed/cancelled tasks"""
        completed_tasks = {task for task in self.active_tasks if task.done()}
        self.active_tasks -= completed_tasks

        logger.debug(f"Cleaned up {len(completed_tasks)} completed tasks")

    def __del__(self):
        """Cleanup when handler is destroyed"""
        if self._executor:
            self._executor.shutdown(wait=False)


# Streamlit Session State Management
class StreamlitSessionManager:
    """
    Manages Streamlit session state for async operations
    Ensures data persistence and prevents loss during reruns
    """

    @staticmethod
    def set_workflow_result(key: str, result: Dict[str, Any]) -> None:
        """Store workflow result in session state with validation"""
        try:
            # Validate result structure
            required_keys = ["status", "summary", "q_and_a", "bullet_points"]
            if not all(k in result for k in required_keys):
                logger.warning(f"Result missing required keys: {required_keys}")

            # Store with timestamp
            st.session_state[key] = {
                **result,
                "_stored_at": datetime.now().isoformat(),
                "_storage_key": key
            }

            logger.info(f"Workflow result stored in session state: {key}")

        except Exception as e:
            logger.error(f"Failed to store session state: {e}")
            # Store minimal fallback
            st.session_state[key] = {
                "status": "storage_error",
                "error": str(e),
                "summary": "Failed to store results in session state"
            }

    @staticmethod
    def get_workflow_result(key: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow result from session state"""
        try:
            result = st.session_state.get(key)
            if result and isinstance(result, dict):
                logger.debug(f"Retrieved workflow result from session: {key}")
                return result
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve session state: {e}")
            return None

    @staticmethod
    def clear_workflow_result(key: str) -> None:
        """Clear workflow result from session state"""
        try:
            if key in st.session_state:
                del st.session_state[key]
                logger.debug(f"Cleared session state: {key}")
        except Exception as e:
            logger.error(f"Failed to clear session state: {e}")

    @staticmethod
    @contextmanager
    def progress_tracker(message: str = "Processing..."):
        """Context manager for Streamlit progress tracking"""
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(msg: str):
            status_text.text(msg)

        try:
            status_text.text(message)
            yield update_progress
        finally:
            progress_bar.progress(100)
            status_text.text("Completed!")


# Global handler instance
_async_handler = None


def get_async_handler() -> StreamlitAsyncHandler:
    """Get singleton async handler instance"""
    global _async_handler
    if _async_handler is None:
        _async_handler = StreamlitAsyncHandler()
    return _async_handler


# Convenience functions for common use cases
def run_workflow_async(
    workflow_func: Awaitable[Any],
    task_name: str = "workflow",
    session_key: str = "workflow_results",
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Run workflow asynchronously with proper Streamlit integration

    Args:
        workflow_func: Async workflow function
        task_name: Name for logging
        session_key: Session state key for results
        timeout: Timeout in seconds

    Returns:
        Workflow results dictionary
    """
    handler = get_async_handler()
    session_manager = StreamlitSessionManager()

    # Check if results already exist
    existing_result = session_manager.get_workflow_result(session_key)
    if existing_result and existing_result.get("status") == "success":
        logger.info("Using cached workflow results")
        return existing_result

    # Show initial progress message
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("Processing document...")

    try:
        # Run async workflow without progress callback to avoid thread context issues
        result = handler.run_async_task(
            coro=workflow_func,
            task_name=task_name,
            timeout=timeout,
            progress_callback=None  # Disable progress callback to avoid Streamlit context issues
        )

        # Update progress
        progress_bar.progress(100)
        status_text.text("Processing completed!")

        # Store results
        session_manager.set_workflow_result(session_key, result)

        return result

    except TimeoutError:
        error_result = {
            "status": "timeout",
            "error": f"Processing timed out after {timeout} seconds",
            "summary": "Document processing was interrupted due to timeout.",
            "q_and_a": "**Why did it timeout?**\n\nThe document may be very large or the service is experiencing high load.",
            "bullet_points": "## Timeout\n\n- Status: ⏱️ Timed out\n- Suggestion: Try again or use smaller document"
        }
        session_manager.set_workflow_result(session_key, error_result)
        return error_result

    except Exception as e:
        # Handle OpenAI API key missing specifically
        if "OPENAI_API_KEY" in str(e):
            error_result = {
                "status": "api_key_missing",
                "error": "OpenAI API key not configured",
                "summary": "Document processing requires an OpenAI API key for content enhancement. The document was parsed but enhanced features are unavailable.",
                "q_and_a": "**Why is an API key needed?**\n\nThe Enhanced Workflow V2 uses OpenAI GPT-4 to generate intelligent summaries, Q&A pairs, and topics from your document content.\n\n**How do I set it up?**\n\nRun `setup_api_key.bat` or set the OPENAI_API_KEY environment variable with your OpenAI API key.",
                "bullet_points": "## Setup Required\n\n- Status: ⚠️ API Key Missing\n- Action: Run setup_api_key.bat\n- Feature: Enhanced content generation unavailable\n- Basic processing: Still functional"
            }
        else:
            error_result = {
                "status": "error",
                "error": str(e),
                "summary": "Document processing failed due to a technical error.",
                "q_and_a": "**What happened?**\n\nA technical error occurred. Please try again or contact support.",
                "bullet_points": "## Error\n\n- Status: ❌ Failed\n- Action: Try again"
            }
        session_manager.set_workflow_result(session_key, error_result)
        return error_result


# Integration with enhanced workflow
def run_enhanced_workflow_streamlit(
    file_path: str,
    document_title: str,
    session_key: str = "enhanced_workflow_results"
) -> Dict[str, Any]:
    """
    Run enhanced workflow v2 with Streamlit integration
    Solves all async issues and preserves session state
    """
    from .enhanced_workflow_v2 import run_enhanced_workflow_v2

    logger.info(f"Starting enhanced workflow for Streamlit: {document_title}")

    # Run with proper async handling
    return run_workflow_async(
        workflow_func=run_enhanced_workflow_v2(file_path, document_title),
        task_name=f"enhanced_workflow_{document_title}",
        session_key=session_key,
        timeout=600  # 10 minutes for large documents
    )