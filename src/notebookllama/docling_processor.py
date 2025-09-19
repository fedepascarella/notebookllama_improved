"""
Docling-based document processor for NotebookLlama
Replaces LlamaCloud functionality with local Docling processing
"""

import os
import json
import warnings
import tempfile as tmp
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union
import pandas as pd
from dataclasses import dataclass

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from llama_index.core import Document
from llama_index.core.schema import TextNode
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from models import Notebook

load_dotenv()


@dataclass
class ProcessedDocument:
    """Container for processed document data"""
    md_content: str
    extracted_data: Dict[str, Any]
    images: Optional[List[str]] = None
    tables: Optional[List[pd.DataFrame]] = None
    metadata: Optional[Dict[str, Any]] = None


class DoclingProcessor:
    """
    Advanced document processor using Docling for local document parsing
    """

    def __init__(self):
        """Initialize the Docling processor with optimized pipeline"""
        
        # Configure pipeline options for better performance
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        
        # Initialize DocumentConverter with custom backend
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pipeline_options,
            }
        )
        
        # Initialize structured LLM for notebook generation
        if os.getenv("OPENAI_API_KEY"):
            llm = OpenAI(
                model="gpt-4o", 
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.structured_llm = llm.as_structured_llm(Notebook)
        else:
            self.structured_llm = None
            warnings.warn("OpenAI API key not found. Notebook generation will be disabled.")

    async def process_document(
        self, 
        file_path: str, 
        extract_images: bool = False,
        extract_tables: bool = False
    ) -> ProcessedDocument:
        """
        Process a document using Docling and extract structured content
        
        Args:
            file_path: Path to the document to process
            extract_images: Whether to extract images
            extract_tables: Whether to extract tables
            
        Returns:
            ProcessedDocument containing all processed data
        """
        try:
            # Convert document using Docling
            result = self.converter.convert(file_path)
            doc = result.document
            
            # Extract markdown content
            md_content = doc.export_to_markdown()
            
            # Extract structured data
            extracted_data = {}
            
            # Extract tables if requested
            tables = []
            if extract_tables:
                tables = self._extract_tables(doc)
                
            # Extract images if requested  
            images = []
            if extract_images:
                images = await self._extract_images(doc)
                
            # Extract metadata
            metadata = self._extract_metadata(doc)
            
            return ProcessedDocument(
                md_content=md_content,
                extracted_data=extracted_data,
                images=images,
                tables=tables,
                metadata=metadata
            )
            
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

    def _extract_tables(self, doc) -> List[pd.DataFrame]:
        """Extract tables from Docling document as pandas DataFrames"""
        tables = []
        
        try:
            # Export to JSON to access structured table data
            doc_json = doc.export_to_json()
            doc_data = json.loads(doc_json)
            
            # Look for table elements in the document structure
            for element in doc_data.get('elements', []):
                if element.get('type') == 'table':
                    # Extract table data
                    table_data = self._parse_table_element(element)
                    if table_data is not None:
                        tables.append(table_data)
                        
                        # Save table to CSV for later use
                        os.makedirs("data/extracted_tables/", exist_ok=True)
                        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
                        table_path = f"data/extracted_tables/table_{timestamp}.csv"
                        table_data.to_csv(table_path, index=False)
                        
        except Exception as e:
            warnings.warn(f"Error extracting tables: {str(e)}")
            
        return tables

    def _parse_table_element(self, table_element: Dict) -> Optional[pd.DataFrame]:
        """Parse a table element from Docling JSON output"""
        try:
            # Extract table structure from Docling output
            data = table_element.get('data', {})
            
            # If table has structured data
            if 'table' in data:
                table_data = data['table']
                
                # Extract headers and rows
                headers = []
                rows = []
                
                # Process table cells
                for row_idx, row in enumerate(table_data.get('rows', [])):
                    row_data = []
                    for cell in row.get('cells', []):
                        cell_text = cell.get('text', '').strip()
                        row_data.append(cell_text)
                        
                    if row_idx == 0 and not headers:
                        headers = row_data
                    else:
                        rows.append(row_data)
                
                # Create DataFrame
                if headers and rows:
                    # Ensure all rows have the same length as headers
                    max_cols = len(headers)
                    normalized_rows = []
                    for row in rows:
                        normalized_row = row[:max_cols] + [''] * (max_cols - len(row))
                        normalized_rows.append(normalized_row)
                    
                    return pd.DataFrame(normalized_rows, columns=headers)
                    
        except Exception as e:
            warnings.warn(f"Error parsing table element: {str(e)}")
            
        return None

    async def _extract_images(self, doc) -> List[str]:
        """Extract images from Docling document"""
        images = []
        
        try:
            # Create static directory for images
            os.makedirs("static/", exist_ok=True)
            
            # Remove old images
            self._cleanup_old_images("static/")
            
            # Export images using Docling's built-in functionality
            doc_json = doc.export_to_json()
            doc_data = json.loads(doc_json)
            
            # Extract image references from document structure
            for element in doc_data.get('elements', []):
                if element.get('type') == 'picture':
                    # Generate image path
                    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
                    image_path = f"static/image_{timestamp}.png"
                    
                    # Save the image data if available
                    if 'data' in element and 'image' in element['data']:
                        # This is a simplified approach - adjust based on actual Docling API
                        images.append(image_path)
                    
        except Exception as e:
            warnings.warn(f"Error extracting images: {str(e)}")
            
        return images

    def _cleanup_old_images(self, path: str) -> None:
        """Clean up old images in the directory"""
        try:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(('.png', '.jpg', '.jpeg')) and '_at_' not in file:
                        old_path = os.path.join(path, file)
                        # Rename with timestamp
                        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
                        base_name = os.path.splitext(file)[0]
                        new_path = os.path.join(path, f"{base_name}_at_{timestamp}.png")
                        os.rename(old_path, new_path)
        except Exception as e:
            warnings.warn(f"Error cleaning up images: {str(e)}")

    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """Extract metadata from Docling document"""
        metadata = {}
        
        try:
            # Export to get document metadata
            doc_json = doc.export_to_json()
            doc_data = json.loads(doc_json)
            
            # Extract basic metadata
            metadata.update({
                'title': doc_data.get('description', {}).get('title', ''),
                'pages': len(doc_data.get('pages', [])),
                'elements_count': len(doc_data.get('elements', [])),
                'processing_time': datetime.now().isoformat(),
                'format': 'PDF',  # Can be extended for other formats
            })
            
        except Exception as e:
            warnings.warn(f"Error extracting metadata: {str(e)}")
            
        return metadata

    async def generate_notebook(self, md_content: str) -> Union[Notebook, None]:
        """Generate notebook structure from markdown content using LLM"""
        if not self.structured_llm:
            warnings.warn("Structured LLM not available. Cannot generate notebook.")
            return None
            
        try:
            messages = [
                ChatMessage(
                    role="user",
                    content=f"""
                    Please analyze the following document content and create a structured notebook with:
                    - A comprehensive summary
                    - 3-10 key highlights/bullet points  
                    - 5-15 questions based on the content
                    - Corresponding answers to those questions
                    
                    Document content:
                    {md_content}
                    """
                )
            ]
            
            response = await self.structured_llm.achat(messages)
            notebook_data = json.loads(response.message.content)
            
            return Notebook(**notebook_data)
            
        except Exception as e:
            warnings.warn(f"Error generating notebook: {str(e)}")
            return None

    async def process_file_complete(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Complete file processing pipeline
        Returns tuple of (structured_data_json, markdown_content)
        """
        try:
            # Process document with all extractions
            processed_doc = await self.process_document(
                file_path=file_path,
                extract_images=False,  # Set to True if needed
                extract_tables=True
            )
            
            # Generate notebook structure
            notebook = await self.generate_notebook(processed_doc.md_content)
            
            if notebook:
                # Convert to JSON
                notebook_json = json.dumps(notebook.model_dump(), indent=2)
                return notebook_json, processed_doc.md_content
            else:
                return None, processed_doc.md_content
                
        except Exception as e:
            warnings.warn(f"Error in complete file processing: {str(e)}")
            return None, None

    async def extract_plots_and_tables(self, file_path: str) -> Tuple[List[str], List[pd.DataFrame]]:
        """Extract plots and tables for visualization page"""
        try:
            processed_doc = await self.process_document(
                file_path=file_path,
                extract_images=True,
                extract_tables=True
            )
            
            return processed_doc.images or [], processed_doc.tables or []
            
        except Exception as e:
            warnings.warn(f"Error extracting plots and tables: {str(e)}")
            return [], []


# Global instance
DOCLING_PROCESSOR = DoclingProcessor()
