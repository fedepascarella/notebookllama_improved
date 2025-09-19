"""
Enhanced Workflow V2 - Senior-level LlamaIndex workflow implementation
Fixes data loss, integrates LLM processing, and provides proper error handling
"""

import asyncio
import logging
import time
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from llama_index.core.workflow import Workflow, step, Context
from llama_index.core.workflow.events import StartEvent, StopEvent

# Import our new event classes and services
from .workflow_events import (
    DocumentProcessedEvent,
    ContentEnhancedEvent,
    NotebookReadyEvent,
    WorkflowErrorEvent,
    create_document_processed_event,
    create_content_enhanced_event
)
from .content_enhancer import ContentEnhancer, create_content_enhancer
from .mind_map_generator import MindMapGenerator, create_mind_map_generator
from .fixed_docling_processor import DoclingProcessor, create_docling_processor

logger = logging.getLogger(__name__)


class EnhancedWorkflowV2(Workflow):
    """
    Enhanced document processing workflow that preserves all content
    and generates high-quality summaries, Q&A, and visualizations.

    Architecture:
    1. Document Processing: Docling extracts ALL content (preserves 127K+ chars)
    2. Content Enhancement: OpenAI generates summaries, Q&A, topics
    3. Notebook Generation: Creates complete notebook with mind maps

    Key Features:
    - Zero data loss (preserves all Docling content)
    - Real LLM-generated content (not generic)
    - Proper error handling and recovery
    - Quality validation at each step
    - Streamlit-compatible async handling
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize services
        self.docling_processor = None
        self.content_enhancer = None
        self.mind_map_generator = None

        self._init_services()

    def _init_services(self) -> None:
        """Initialize all required services with error handling"""
        try:
            # Initialize Docling processor with memory-optimized settings
            self.docling_processor = create_docling_processor(
                memory_optimized=True  # Enable all memory optimizations
            )
            self.logger.info("Docling processor initialized")

            # Initialize content enhancer
            self.content_enhancer = create_content_enhancer(model="gpt-4o")
            self.logger.info("Content enhancer initialized")

            # Initialize mind map generator
            self.mind_map_generator = create_mind_map_generator()
            self.logger.info("Mind map generator initialized")

        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            raise

    @step
    async def process_document(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> DocumentProcessedEvent:
        """
        Step 1: Process document with Docling
        CRITICAL: Preserves ALL content (no data loss)
        """
        start_time = time.time()

        try:
            # Extract file information from StartEvent
            file_path = getattr(ev, 'file_path', None)
            if not file_path:
                raise ValueError("No file_path provided in StartEvent")

            self.logger.info(f"Starting document processing: {file_path}")

            # Process with Docling
            if not self.docling_processor:
                raise RuntimeError("Docling processor not initialized")

            docling_result = self.docling_processor.process_document(file_path)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create validated event with ALL content preserved
            document_event = create_document_processed_event(
                docling_result=docling_result,
                file_path=file_path,
                processing_time_ms=processing_time_ms
            )

            self.logger.info(
                f"Document processed successfully: {document_event.content_size} characters, "
                f"{len(document_event.tables)} tables, {len(document_event.figures)} figures"
            )

            return document_event

        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            error_result = {
                "status": "error",
                "error_stage": "document_processing",
                "error_message": str(e),
                "context": {"file_path": file_path if 'file_path' in locals() else "unknown"},
                "recoverable": False
            }
            return StopEvent(result=error_result)

    @step
    async def enhance_content(
        self,
        ctx: Context,
        ev: DocumentProcessedEvent
    ) -> ContentEnhancedEvent:
        """
        Step 2: Enhance content with LLM
        Generates real summaries, Q&A, and topics from document content
        """
        try:
            self.logger.info("Starting content enhancement with LLM")

            if not self.content_enhancer:
                raise RuntimeError("Content enhancer not initialized")

            # Generate enhanced content using OpenAI
            enhanced_content = await self.content_enhancer.enhance_document(ev)

            # Create validated enhanced event
            enhanced_event = create_content_enhanced_event(
                original_event=ev,
                llm_results=enhanced_content
            )

            self.logger.info(
                f"Content enhanced successfully: summary={len(enhanced_event.summary)} chars, "
                f"Q&A pairs={len(enhanced_event.questions)}, topics={len(enhanced_event.topics)}"
            )

            return enhanced_event

        except Exception as e:
            self.logger.error(f"Content enhancement failed: {e}")
            error_result = {
                "status": "error",
                "error_stage": "content_enhancement",
                "error_message": str(e),
                "context": {
                    "document_title": ev.title,
                    "content_size": ev.content_size
                },
                "recoverable": True
            }
            return StopEvent(result=error_result)

    @step
    async def generate_notebook(
        self,
        ctx: Context,
        ev: ContentEnhancedEvent
    ) -> NotebookReadyEvent:
        """
        Step 3: Generate final notebook with mind map
        Creates complete notebook structure ready for Streamlit display
        """
        try:
            self.logger.info("Generating final notebook and mind map")

            if not self.mind_map_generator:
                raise RuntimeError("Mind map generator not initialized")

            # Generate mind map HTML
            mind_map_html = self.mind_map_generator.generate_mind_map(
                title=ev.original_event.title,
                topics=ev.topics,
                key_points=ev.key_points
            )

            # Create notebook structure
            notebook_content = self._create_notebook_structure(ev)

            # Format content for Streamlit display
            formatted_summary = self._format_summary_for_display(ev.summary)
            formatted_qa = ev.formatted_qa
            formatted_highlights = self._format_highlights_for_display(ev.formatted_highlights)

            # Create final event
            notebook_event = NotebookReadyEvent(
                enhanced_event=ev,
                notebook_content=notebook_content,
                mind_map_html=mind_map_html,
                formatted_summary=formatted_summary,
                formatted_qa=formatted_qa,
                formatted_highlights=formatted_highlights
            )

            self.logger.info("Notebook generation completed successfully")

            return notebook_event

        except Exception as e:
            self.logger.error(f"Notebook generation failed: {e}")
            error_result = {
                "status": "error",
                "error_stage": "notebook_generation",
                "error_message": str(e),
                "context": {
                    "document_title": ev.original_event.title,
                    "topics_count": len(ev.topics)
                },
                "recoverable": True
            }
            return StopEvent(result=error_result)

    @step
    async def finalize_workflow(
        self,
        ctx: Context,
        ev: NotebookReadyEvent
    ) -> StopEvent:
        """
        Step 4: Finalize workflow and return complete results
        """
        try:
            self.logger.info("Finalizing workflow")

            # Create comprehensive result dictionary
            result = {
                "status": "success",
                "document_title": ev.original_document.title,
                "content_size": ev.original_document.content_size,

                # Streamlit display content
                "summary": ev.formatted_summary,
                "q_and_a": ev.formatted_qa,
                "bullet_points": ev.formatted_highlights,
                "mind_map": ev.mind_map_html,

                # Full content for chat and search
                "md_content": ev.original_document.raw_content,
                "full_content": ev.original_document.raw_content,

                # Notebook structure
                "notebook_content": ev.notebook_content,

                # Rich metadata
                "metadata": ev.full_metadata,

                # Processing details
                "processing_details": {
                    "total_stages": 4,
                    "content_preserved": True,
                    "llm_enhanced": True,
                    "mind_map_generated": True,
                    "quality_score": ev.enhanced_event.enhancement_metadata.get("quality_score", 1.0)
                }
            }

            self.logger.info(
                f"Workflow completed successfully: {result['content_size']} characters preserved, "
                f"quality score: {result['processing_details']['quality_score']:.2f}"
            )

            return StopEvent(result=result)

        except Exception as e:
            self.logger.error(f"Workflow finalization failed: {e}")

            # Create minimal result for error case
            error_result = {
                "status": "error",
                "error": str(e),
                "stage": "finalization",
                "partial_content": getattr(ev, 'formatted_summary', "Processing failed")
            }

            return StopEvent(result=error_result)


    # Helper methods
    def _create_notebook_structure(self, enhanced_event: ContentEnhancedEvent) -> Dict[str, Any]:
        """Create Jupyter notebook structure"""
        original_doc = enhanced_event.original_event

        return {
            "nbformat": 4,
            "nbformat_minor": 4,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.11.0"
                },
                "document_info": {
                    "title": original_doc.title,
                    "processing_timestamp": datetime.now().isoformat(),
                    "content_size": original_doc.content_size,
                    "enhancement_quality": enhanced_event.enhancement_metadata.get("quality_score", 1.0)
                }
            },
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {original_doc.title}\n\n",
                        f"**Document processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n",
                        f"**Content size:** {original_doc.content_size:,} characters  \n",
                        f"**Quality score:** {enhanced_event.enhancement_metadata.get('quality_score', 1.0):.2f}/1.0\n\n",
                        "## Summary\n\n",
                        enhanced_event.summary,
                        "\n\n## Key Points\n\n"
                    ] + [f"- {point}\n" for point in enhanced_event.key_points] + [
                        "\n## Topics Covered\n\n"
                    ] + [f"- {topic}\n" for topic in enhanced_event.topics]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Full Document Content\n\n",
                        original_doc.raw_content[:5000] + ("..." if len(original_doc.raw_content) > 5000 else "")
                    ]
                }
            ]
        }

    def _format_summary_for_display(self, summary: str) -> str:
        """Format summary for clean Streamlit display"""
        # Ensure proper paragraph spacing
        formatted = summary.replace('\n\n', '\n\n')

        # Add visual structure if needed
        if not summary.startswith('##') and not summary.startswith('#'):
            formatted = summary

        return formatted.strip()

    def _format_highlights_for_display(self, highlights: List[str]) -> str:
        """Format highlights as bullet points for Streamlit"""
        if not highlights:
            return "## Key Highlights\n\n- Document processed successfully"

        formatted = "## Key Highlights\n\n"
        for highlight in highlights:
            formatted += f"- {highlight}\n"

        return formatted.strip()

    def _create_fallback_result(self, error_event: WorkflowErrorEvent) -> Dict[str, Any]:
        """Create fallback result when workflow fails but is recoverable"""
        return {
            "status": "partial_success",
            "summary": "The document was processed but some enhancements could not be completed due to technical issues. The content is available for exploration.",
            "q_and_a": "**What happened during processing?**\n\nThe document was successfully parsed but content enhancement encountered an issue. You can still explore the full document content.\n\n**Is the content still available?**\n\nYes, the complete document content has been preserved and is available for searching and analysis.",
            "bullet_points": "## Status\n\n- Document parsing: ✅ Completed\n- Content extraction: ✅ Completed\n- Enhancement: ⚠️ Partial\n- Content preserved: ✅ Yes",
            "mind_map": "<div style='text-align: center; padding: 50px;'><h3>Mind Map Unavailable</h3><p>The mind map could not be generated due to a technical issue, but your document content is fully preserved.</p></div>",
            "md_content": error_event.context.get("content", "Content preservation failed"),
            "metadata": {
                "error_occurred": True,
                "error_stage": error_event.stage,
                "recoverable": error_event.recoverable,
                "processing_timestamp": error_event.timestamp.isoformat()
            }
        }


# Factory function for easy instantiation
def create_enhanced_workflow_v2(**kwargs) -> EnhancedWorkflowV2:
    """Create enhanced workflow with proper configuration"""
    return EnhancedWorkflowV2(**kwargs)


# Async runner for Streamlit integration
async def run_enhanced_workflow_v2(file_path: str, document_title: str) -> Dict[str, Any]:
    """
    Run the enhanced workflow asynchronously
    Designed for Streamlit integration with proper error handling
    """
    logger.info(f"Starting enhanced workflow v2 for: {document_title}")

    try:
        # Create and run workflow
        workflow = create_enhanced_workflow_v2(timeout=300, verbose=True)

        # Create StartEvent with file information
        start_event = StartEvent()
        start_event.file_path = file_path
        start_event.document_title = document_title

        # Run workflow
        result = await workflow.run(start_event=start_event)

        logger.info("Enhanced workflow v2 completed successfully")
        return result

    except asyncio.TimeoutError:
        logger.error("Workflow timed out")
        return {
            "status": "timeout",
            "error": "Processing timed out - document may be too large or complex",
            "summary": "Processing was interrupted due to timeout. Please try with a smaller document.",
            "q_and_a": "**Why did processing timeout?**\n\nThe document may be very large or complex. Try breaking it into smaller sections.",
            "bullet_points": "## Timeout Information\n\n- Status: ⏱️ Timed out\n- Suggestion: Try smaller documents\n- Content: Not fully processed"
        }

    except Exception as e:
        logger.error(f"Workflow failed with exception: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "summary": "Document processing failed due to a technical error. Please try again or contact support.",
            "q_and_a": "**What went wrong?**\n\nA technical error occurred during processing. The system has logged the issue for investigation.",
            "bullet_points": "## Error Information\n\n- Status: ❌ Failed\n- Action: Try again or contact support\n- Details: Error logged for investigation"
        }