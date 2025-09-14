"""
Enhanced workflow using Docling and PostgreSQL
Replaces LlamaCloud dependency with local processing
"""

import json
import uuid
from typing import List, Union

from llama_index.workflows import Workflow, step, Context
from llama_index.workflows.events import StartEvent, StopEvent, Event
from llama_index.workflows.resource import Resource

from docling_processor import DOCLING_PROCESSOR
from postgres_manager import DOCUMENT_MANAGER, EnhancedDocument
from mindmap import get_mind_map


class FileInputEvent(StartEvent):
    file: str


class NotebookOutputEvent(StopEvent):
    mind_map: str
    md_content: str
    summary: str
    highlights: List[str]
    questions: List[str]
    answers: List[str]


class MindMapCreationEvent(Event):
    summary: str
    highlights: List[str]
    questions: List[str]
    answers: List[str]
    md_content: str
    document_id: str


def get_docling_processor(*args, **kwargs):
    """Resource function for Docling processor"""
    return DOCLING_PROCESSOR


def get_document_manager(*args, **kwargs):
    """Resource function for document manager"""
    return DOCUMENT_MANAGER


class EnhancedNotebookLMWorkflow(Workflow):
    """
    Enhanced workflow using Docling for document processing and PostgreSQL for storage
    """

    @step
    async def extract_file_data(
        self,
        ev: FileInputEvent,
        processor: Resource[get_docling_processor],
        doc_manager: Resource[get_document_manager],
        ctx: Context,
    ) -> Union[MindMapCreationEvent, NotebookOutputEvent]:
        """Extract and process file data using Docling"""
        
        ctx.write_event_to_stream(ev=ev)
        
        try:
            # Process file using Docling
            notebook_json, md_content = await processor.process_file_complete(ev.file)
            
            if notebook_json is None:
                return NotebookOutputEvent(
                    mind_map="❌ Document processing failed",
                    md_content="",
                    summary="Could not process the uploaded document",
                    highlights=[],
                    questions=[],
                    answers=[],
                )
            
            # Parse the notebook data
            notebook_data = json.loads(notebook_json)
            
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Create enhanced document for storage
            enhanced_doc = EnhancedDocument(
                id=document_id,
                document_name=f"Document_{document_id[:8]}",  # Temporary name, will be updated
                content=md_content or "",
                summary=notebook_data.get("summary", ""),
                q_and_a="",  # Will be populated later
                mindmap="",  # Will be populated later
                bullet_points="",  # Will be populated later
                metadata={
                    "processed_by": "docling",
                    "file_path": ev.file,
                    "processing_status": "completed"
                },
                is_processed=True
            )
            
            # Store document in PostgreSQL
            try:
                await doc_manager.put_document(enhanced_doc)
            except Exception as storage_error:
                print(f"Warning: Could not store document in database: {storage_error}")
            
            return MindMapCreationEvent(
                md_content=md_content or "",
                document_id=document_id,
                **notebook_data,
            )
            
        except Exception as e:
            print(f"Error in extract_file_data: {str(e)}")
            return NotebookOutputEvent(
                mind_map="❌ Processing error occurred",
                md_content="",
                summary=f"Error processing document: {str(e)}",
                highlights=[],
                questions=[],
                answers=[],
            )

    @step
    async def generate_mind_map(
        self,
        ev: MindMapCreationEvent,
        doc_manager: Resource[get_document_manager],
        ctx: Context,
    ) -> NotebookOutputEvent:
        """Generate mind map and finalize document processing"""
        
        ctx.write_event_to_stream(ev=ev)
        
        try:
            # Generate mind map
            mind_map_result = await get_mind_map(ev.summary, ev.highlights)
            mind_map_content = mind_map_result if mind_map_result else "❌ Mind map generation failed"
            
            # Prepare Q&A content
            q_and_a = ""
            for q, a in zip(ev.questions, ev.answers):
                q_and_a += f"**{q}**\n\n{a}\n\n"
            
            # Prepare bullet points
            bullet_points = "## Key Highlights\n\n- " + "\n- ".join(ev.highlights)
            
            # Update document in database with complete information
            try:
                # Retrieve existing document
                session = doc_manager.get_session()
                from postgres_manager import DocumentRecord
                
                doc_record = session.query(DocumentRecord).filter(
                    DocumentRecord.id == ev.document_id
                ).first()
                
                if doc_record:
                    # Update with complete information
                    doc_record.q_and_a = q_and_a
                    doc_record.mindmap = mind_map_content
                    doc_record.bullet_points = bullet_points
                    doc_record.metadata = {
                        **doc_record.metadata,
                        "mind_map_generated": mind_map_result is not None,
                        "questions_count": len(ev.questions),
                        "highlights_count": len(ev.highlights)
                    }
                    
                    session.commit()
                    
                session.close()
                
            except Exception as update_error:
                print(f"Warning: Could not update document in database: {update_error}")
            
            return NotebookOutputEvent(
                mind_map=mind_map_content,
                md_content=ev.md_content,
                summary=ev.summary,
                highlights=ev.highlights,
                questions=ev.questions,
                answers=ev.answers,
            )
            
        except Exception as e:
            print(f"Error in generate_mind_map: {str(e)}")
            return NotebookOutputEvent(
                mind_map="❌ Mind map generation failed",
                md_content=ev.md_content,
                summary=ev.summary,
                highlights=ev.highlights,
                questions=ev.questions,
                answers=ev.answers,
            )


# Enhanced workflow instance
WF = EnhancedNotebookLMWorkflow(timeout=600)
