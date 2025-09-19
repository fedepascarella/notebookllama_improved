"""
Enhanced Workflow Events - Type-safe event classes for document processing pipeline
Senior-level implementation with proper validation, error handling, and documentation
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging
from pydantic import BaseModel, Field, validator, root_validator

from llama_index.core.workflow.events import Event

logger = logging.getLogger(__name__)


class DocumentProcessedEvent(Event):
    """
    Event emitted after successful Docling document processing.
    Contains complete document data with validation.
    """

    def __init__(
        self,
        raw_content: str,
        title: str,
        metadata: Dict[str, Any],
        tables: Optional[List[Dict[str, Any]]] = None,
        figures: Optional[List[Dict[str, Any]]] = None,
        file_path: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        **kwargs
    ):
        super().__init__()

        # Validate inputs
        if not raw_content or len(raw_content.strip()) < 10:
            raise ValueError("raw_content must be non-empty and substantial")

        if not title or len(title.strip()) < 1:
            raise ValueError("title must be non-empty")

        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary")

        # Store validated data
        self.raw_content = raw_content.strip()
        self.title = title.strip()
        self.metadata = metadata
        self.tables = tables or []
        self.figures = figures or []
        self.file_path = file_path
        self.processing_time_ms = processing_time_ms
        self.timestamp = datetime.now()

        # Log successful creation
        logger.info(
            f"DocumentProcessedEvent created: {len(self.raw_content)} chars, "
            f"{len(self.tables)} tables, {len(self.figures)} figures"
        )

    @property
    def content_size(self) -> int:
        """Get content size in characters"""
        return len(self.raw_content)

    @property
    def has_tables(self) -> bool:
        """Check if document has tables"""
        return len(self.tables) > 0

    @property
    def has_figures(self) -> bool:
        """Check if document has figures"""
        return len(self.figures) > 0

    def get_content_preview(self, max_chars: int = 500) -> str:
        """Get truncated content preview"""
        if len(self.raw_content) <= max_chars:
            return self.raw_content
        return self.raw_content[:max_chars] + "..."


class ContentEnhancedEvent(Event):
    """
    Event emitted after LLM content enhancement.
    Contains AI-generated summaries, Q&A, and extracted topics.
    """

    def __init__(
        self,
        original_event: DocumentProcessedEvent,
        summary: str,
        key_points: List[str],
        questions: List[str],
        answers: List[str],
        topics: List[str],
        enhancement_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__()

        # Validate inputs
        if not isinstance(original_event, DocumentProcessedEvent):
            raise ValueError("original_event must be DocumentProcessedEvent")

        if not summary or len(summary.strip()) < 50:
            raise ValueError("summary must be substantial (min 50 chars)")

        if len(questions) != len(answers):
            raise ValueError("questions and answers must have same length")

        if len(questions) < 3:
            raise ValueError("must have at least 3 Q&A pairs")

        if len(key_points) < 3:
            raise ValueError("must have at least 3 key points")

        # Store validated data
        self.original_event = original_event
        self.summary = summary.strip()
        self.key_points = [point.strip() for point in key_points]
        self.questions = [q.strip() for q in questions]
        self.answers = [a.strip() for a in answers]
        self.topics = [topic.strip() for topic in topics]
        self.enhancement_metadata = enhancement_metadata or {}
        self.timestamp = datetime.now()

        logger.info(
            f"ContentEnhancedEvent created: {len(self.summary)} char summary, "
            f"{len(self.questions)} Q&A pairs, {len(self.topics)} topics"
        )

    @property
    def formatted_qa(self) -> str:
        """Format Q&A for display"""
        formatted = ""
        for q, a in zip(self.questions, self.answers):
            formatted += f"**{q}**\n\n{a}\n\n"
        return formatted.strip()

    @property
    def formatted_highlights(self) -> List[str]:
        """Format key points as highlights"""
        return [f"🔹 {point}" for point in self.key_points]


class NotebookReadyEvent(Event):
    """
    Event emitted when complete notebook is ready for UI display.
    Contains all processed data formatted for Streamlit.
    """

    def __init__(
        self,
        enhanced_event: ContentEnhancedEvent,
        notebook_content: Dict[str, Any],
        mind_map_html: str,
        formatted_summary: str,
        formatted_qa: str,
        formatted_highlights: str,
        **kwargs
    ):
        super().__init__()

        # Validate inputs
        if not isinstance(enhanced_event, ContentEnhancedEvent):
            raise ValueError("enhanced_event must be ContentEnhancedEvent")

        if not isinstance(notebook_content, dict):
            raise ValueError("notebook_content must be a dictionary")

        if not mind_map_html or len(mind_map_html.strip()) < 50:
            raise ValueError("mind_map_html must be substantial")

        # Store validated data
        self.enhanced_event = enhanced_event
        self.notebook_content = notebook_content
        self.mind_map_html = mind_map_html
        self.formatted_summary = formatted_summary
        self.formatted_qa = formatted_qa
        self.formatted_highlights = formatted_highlights
        self.timestamp = datetime.now()

        logger.info("NotebookReadyEvent created - ready for UI display")

    @property
    def original_document(self) -> DocumentProcessedEvent:
        """Get original document event"""
        return self.enhanced_event.original_event

    @property
    def full_metadata(self) -> Dict[str, Any]:
        """Get complete metadata from all processing stages"""
        return {
            **self.original_document.metadata,
            **self.enhanced_event.enhancement_metadata,
            "total_processing_stages": 3,
            "final_timestamp": self.timestamp.isoformat(),
            "content_preserved": len(self.original_document.raw_content),
            "summary_generated": len(self.formatted_summary),
            "qa_pairs": len(self.enhanced_event.questions),
            "key_points": len(self.enhanced_event.key_points),
            "topics_identified": len(self.enhanced_event.topics)
        }


class WorkflowErrorEvent(Event):
    """
    Event emitted when workflow encounters an error.
    Provides detailed error information for debugging and recovery.
    """

    def __init__(
        self,
        error: Exception,
        stage: str,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        **kwargs
    ):
        super().__init__()

        self.error = error
        self.stage = stage
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()

        logger.error(
            f"WorkflowErrorEvent in stage '{stage}': {error}",
            extra={"context": self.context, "recoverable": self.recoverable}
        )

    @property
    def error_summary(self) -> str:
        """Get human-readable error summary"""
        return f"Error in {self.stage}: {str(self.error)}"

    @property
    def debug_info(self) -> Dict[str, Any]:
        """Get detailed debug information"""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "stage": self.stage,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "context": self.context
        }


# Validation utilities
class EventValidator:
    """Utility class for validating events"""

    @staticmethod
    def validate_content_quality(content: str) -> bool:
        """Validate if content meets quality standards"""
        if not content or len(content.strip()) < 100:
            return False

        # Check for reasonable word count
        words = content.split()
        if len(words) < 20:
            return False

        # Check for diverse vocabulary (basic heuristic)
        unique_words = set(word.lower() for word in words)
        if len(unique_words) < len(words) * 0.3:  # At least 30% unique words
            return False

        return True

    @staticmethod
    def validate_qa_quality(questions: List[str], answers: List[str]) -> bool:
        """Validate Q&A quality"""
        if len(questions) != len(answers):
            return False

        for q, a in zip(questions, answers):
            if not q.strip() or not a.strip():
                return False

            if len(q.strip()) < 10 or len(a.strip()) < 20:
                return False

            # Question should end with question mark
            if not q.strip().endswith('?'):
                return False

        return True


# Factory functions for easy event creation
def create_document_processed_event(
    docling_result: Dict[str, Any],
    file_path: str,
    processing_time_ms: int
) -> DocumentProcessedEvent:
    """Factory function to create DocumentProcessedEvent from Docling result"""

    try:
        return DocumentProcessedEvent(
            raw_content=docling_result["content"],
            title=docling_result["title"],
            metadata=docling_result["metadata"],
            tables=docling_result.get("tables", []),
            figures=docling_result.get("figures", []),
            file_path=file_path,
            processing_time_ms=processing_time_ms
        )
    except Exception as e:
        logger.error(f"Failed to create DocumentProcessedEvent: {e}")
        raise ValueError(f"Invalid Docling result format: {e}") from e


def create_content_enhanced_event(
    original_event: DocumentProcessedEvent,
    llm_results: Dict[str, Any]
) -> ContentEnhancedEvent:
    """Factory function to create ContentEnhancedEvent from LLM results"""

    try:
        return ContentEnhancedEvent(
            original_event=original_event,
            summary=llm_results["summary"],
            key_points=llm_results["key_points"],
            questions=llm_results["questions"],
            answers=llm_results["answers"],
            topics=llm_results["topics"],
            enhancement_metadata=llm_results.get("metadata", {})
        )
    except Exception as e:
        logger.error(f"Failed to create ContentEnhancedEvent: {e}")
        raise ValueError(f"Invalid LLM results format: {e}") from e


# Type hints for better IDE support
EventType = Union[
    DocumentProcessedEvent,
    ContentEnhancedEvent,
    NotebookReadyEvent,
    WorkflowErrorEvent
]