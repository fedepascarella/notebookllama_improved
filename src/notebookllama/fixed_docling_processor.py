"""
Docling processor corregido para NotebookLlama Enhanced
Basado en la documentación oficial: https://docling-project.github.io/docling/examples/custom_convert/
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Importaciones corregidas para Docling
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, 
    EasyOcrOptions,
    TesseractOcrOptions,
    TableFormerMode
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

# Backends disponibles
try:
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    PYPDFIUM_AVAILABLE = True
except ImportError:
    PYPDFIUM_AVAILABLE = False

try:
    from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
    DOCLING_PARSE_AVAILABLE = True
except ImportError:
    DOCLING_PARSE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class DoclingConfig:
    """Configuración para Docling processor"""
    do_ocr: bool = True
    do_table_structure: bool = True
    do_cell_matching: bool = True
    use_gpu: bool = False
    num_threads: int = 4
    backend_preference: str = "auto"  # "auto", "pypdfium", "docling_parse"
    ocr_engine: str = "easyocr"  # "easyocr", "tesseract"
    table_mode: str = "accurate"  # "accurate", "fast"
    languages: List[str] = None
    enable_remote_services: bool = False

class DoclingProcessor:
    """
    Procesador de documentos usando Docling con manejo de errores mejorado
    """
    
    def __init__(self, config: Optional[DoclingConfig] = None):
        """Initialize the Docling processor with configuration"""
        self.config = config or DoclingConfig()
        if self.config.languages is None:
            self.config.languages = ["en"]
        
        self.converter = self._setup_converter()
        
    def _setup_converter(self) -> DocumentConverter:
        """Setup DocumentConverter with corrected configuration"""
        try:
            # Configurar pipeline options
            pipeline_options = PdfPipelineOptions()
            
            # OCR configuration
            pipeline_options.do_ocr = self.config.do_ocr
            
            if self.config.do_ocr:
                if self.config.ocr_engine == "tesseract":
                    pipeline_options.ocr_options = TesseractOcrOptions()
                else:  # default to easyocr
                    pipeline_options.ocr_options = EasyOcrOptions()
                
                # Set languages
                if hasattr(pipeline_options.ocr_options, 'lang'):
                    pipeline_options.ocr_options.lang = self.config.languages
                
                # GPU settings
                if hasattr(pipeline_options.ocr_options, 'use_gpu'):
                    pipeline_options.ocr_options.use_gpu = self.config.use_gpu
            
            # Table structure configuration
            pipeline_options.do_table_structure = self.config.do_table_structure
            
            if self.config.do_table_structure:
                pipeline_options.table_structure_options.do_cell_matching = self.config.do_cell_matching
                
                # Set TableFormer mode
                if self.config.table_mode == "fast":
                    pipeline_options.table_structure_options.mode = TableFormerMode.FAST
                else:
                    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            
            # Accelerator configuration
            pipeline_options.accelerator_options = AcceleratorOptions(
                num_threads=self.config.num_threads,
                device=AcceleratorDevice.AUTO
            )
            
            # Remote services
            pipeline_options.enable_remote_services = self.config.enable_remote_services
            
            # Determinar el backend a usar
            backend = self._select_backend()
            
            # CORRECCIÓN: El backend va en PdfFormatOption, NO en PdfPipelineOptions
            format_options = {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=backend  # ← AQUÍ va el backend, no en pipeline_options
                )
            }
            
            # Create DocumentConverter
            converter = DocumentConverter(format_options=format_options)
            
            logger.info(f"Docling converter initialized successfully with backend: {backend.__name__}")
            return converter
            
        except Exception as e:
            logger.error(f"Failed to setup Docling converter: {e}")
            # Fallback to basic configuration
            return self._setup_fallback_converter()
    
    def _select_backend(self):
        """Select the appropriate backend based on configuration and availability"""
        if self.config.backend_preference == "pypdfium" and PYPDFIUM_AVAILABLE:
            return PyPdfiumDocumentBackend
        elif self.config.backend_preference == "docling_parse" and DOCLING_PARSE_AVAILABLE:
            return DoclingParseDocumentBackend
        else:
            # Auto selection
            if DOCLING_PARSE_AVAILABLE:
                logger.info("Using DoclingParseDocumentBackend (recommended)")
                return DoclingParseDocumentBackend
            elif PYPDFIUM_AVAILABLE:
                logger.info("Using PyPdfiumDocumentBackend (fallback)")
                return PyPdfiumDocumentBackend
            else:
                logger.warning("No specific backend available, using default")
                # Docling will use its default backend
                return None
    
    def _setup_fallback_converter(self) -> DocumentConverter:
        """Setup basic converter as fallback"""
        try:
            logger.warning("Using basic DocumentConverter as fallback")
            return DocumentConverter()
        except Exception as e:
            logger.error(f"Even fallback converter failed: {e}")
            raise
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document and return structured content
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with processed content and metadata
        """
        try:
            input_path = Path(file_path)
            
            if not input_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"Processing document: {input_path.name}")
            
            # Convert document
            result = self.converter.convert(input_path)
            
            if not result or not result.document:
                raise ValueError("Document conversion failed - no result")
            
            document = result.document
            
            # Extract content
            content = {
                "title": self._extract_title(document),
                "content": document.export_to_markdown(),
                "metadata": {
                    "filename": input_path.name,
                    "file_size": input_path.stat().st_size if input_path.exists() else 0,
                    "pages": len(document.pages) if hasattr(document, 'pages') else 0,
                    "conversion_status": str(result.status) if hasattr(result, 'status') else 'success'
                },
                "tables": self._extract_tables(document),
                "figures": self._extract_figures(document),
                "raw_document": document  # Keep reference for advanced processing
            }
            
            logger.info(f"Successfully processed document with {content['metadata']['pages']} pages")
            return content
            
        except Exception as e:
            logger.error(f"Docling processing failed: {e}")
            
            # Try PyPDF2 fallback
            return self._pypdf2_fallback(file_path)
    
    def _extract_title(self, document) -> str:
        """Extract document title"""
        try:
            # Try to get title from metadata
            if hasattr(document, 'metadata') and document.metadata:
                title = getattr(document.metadata, 'title', None)
                if title:
                    return title
            
            # Fallback: use first heading or first few words
            markdown_content = document.export_to_markdown()
            lines = markdown_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    return line.lstrip('# ').strip()
                elif line and len(line) > 10:
                    # Take first sentence as title
                    words = line.split()[:8]
                    return ' '.join(words) + ('...' if len(line.split()) > 8 else '')
            
            return "Untitled Document"
            
        except Exception as e:
            logger.warning(f"Failed to extract title: {e}")
            return "Untitled Document"
    
    def _extract_tables(self, document) -> List[Dict[str, Any]]:
        """Extract table information"""
        tables = []
        try:
            if hasattr(document, 'tables'):
                for i, table in enumerate(document.tables):
                    table_info = {
                        "index": i,
                        "caption": getattr(table, 'caption', ''),
                        "data": self._table_to_dict(table) if hasattr(table, 'export_to_dataframe') else None
                    }
                    tables.append(table_info)
        except Exception as e:
            logger.warning(f"Failed to extract tables: {e}")
        
        return tables
    
    def _extract_figures(self, document) -> List[Dict[str, Any]]:
        """Extract figure information"""
        figures = []
        try:
            if hasattr(document, 'figures'):
                for i, figure in enumerate(document.figures):
                    figure_info = {
                        "index": i,
                        "caption": getattr(figure, 'caption', ''),
                        "type": getattr(figure, 'type', 'unknown')
                    }
                    figures.append(figure_info)
        except Exception as e:
            logger.warning(f"Failed to extract figures: {e}")
        
        return figures
    
    def _table_to_dict(self, table) -> Optional[Dict[str, Any]]:
        """Convert table to dictionary format"""
        try:
            if hasattr(table, 'export_to_dataframe'):
                df = table.export_to_dataframe()
                return df.to_dict('records')
            return None
        except Exception as e:
            logger.warning(f"Failed to convert table: {e}")
            return None
    
    def _pypdf2_fallback(self, file_path: str) -> Dict[str, Any]:
        """Fallback processing using PyPDF2"""
        try:
            import PyPDF2
            
            logger.info("Attempting PyPDF2 fallback processing")
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            text_content.append(f"## Page {page_num + 1}\n\n{text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                
                full_content = '\n\n'.join(text_content)
                
                return {
                    "title": f"Document (PyPDF2 fallback)",
                    "content": full_content,
                    "metadata": {
                        "filename": Path(file_path).name,
                        "pages": len(pdf_reader.pages),
                        "extraction_method": "pypdf2_fallback",
                        "warning": "Basic text extraction - limited formatting"
                    },
                    "tables": [],
                    "figures": [],
                    "raw_document": None
                }
                
        except ImportError:
            logger.error("PyPDF2 not available for fallback")
            raise RuntimeError("Document processing failed and no fallback available")
        except Exception as e:
            logger.error(f"PyPDF2 fallback also failed: {e}")
            raise RuntimeError(f"All document processing methods failed: {e}")

# Factory function for easy instantiation
def create_docling_processor(
    use_gpu: bool = False,
    backend: str = "auto",
    ocr_engine: str = "easyocr",
    table_mode: str = "accurate",
    memory_optimized: bool = False
) -> DoclingProcessor:
    """
    Create a DoclingProcessor with common configurations

    Args:
        use_gpu: Whether to use GPU acceleration
        backend: Backend preference ("auto", "pypdfium", "docling_parse")
        ocr_engine: OCR engine to use ("easyocr", "tesseract")
        table_mode: TableFormer mode ("accurate", "fast")
        memory_optimized: If True, use memory-conservative settings
    """

    # Apply memory optimizations if requested
    if memory_optimized:
        use_gpu = False  # Force CPU to avoid GPU memory issues
        backend = "pypdfium"  # Lighter backend
        ocr_engine = None  # Disable OCR to save memory and avoid installation issues
        table_mode = "fast"  # Much less memory intensive

    # Create config with memory considerations
    config_kwargs = {
        "use_gpu": use_gpu,
        "backend_preference": backend,
        "table_mode": table_mode
    }

    # Only add OCR engine if specified
    if ocr_engine is not None:
        config_kwargs["ocr_engine"] = ocr_engine

    # Add memory optimizations
    if memory_optimized:
        config_kwargs.update({
            "num_threads": 1,  # Reduce thread count to save memory
            "do_table_structure": False,  # Disable memory-intensive table processing
            "do_cell_matching": False,  # Disable cell matching
            "enable_remote_services": False,  # Avoid remote service overhead
            "do_ocr": False,  # Disable OCR to save memory and avoid engine issues
        })

    config = DoclingConfig(**config_kwargs)
    
    return DoclingProcessor(config)

# Backward compatibility
def process_with_docling(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Process a document with default Docling settings
    
    Args:
        file_path: Path to the document
        **kwargs: Additional configuration options
    """
    processor = create_docling_processor(**kwargs)
    return processor.process_document(file_path)

# Example configurations for different use cases
def create_fast_processor() -> DoclingProcessor:
    """Create processor optimized for speed"""
    config = DoclingConfig(
        do_ocr=True,
        do_table_structure=True,
        do_cell_matching=False,  # Faster
        use_gpu=False,
        backend_preference="pypdfium",
        table_mode="fast"
    )
    return DoclingProcessor(config)

def create_accurate_processor() -> DoclingProcessor:
    """Create processor optimized for accuracy"""
    config = DoclingConfig(
        do_ocr=True,
        do_table_structure=True,
        do_cell_matching=True,  # More accurate
        use_gpu=True,
        backend_preference="docling_parse",
        table_mode="accurate"
    )
    return DoclingProcessor(config)

if __name__ == "__main__":
    # Test the processor
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    processor = create_docling_processor()
    
    # This would process a document if you have one
    # result = processor.process_document("path/to/your/document.pdf")
    # print(result["title"])
    
    print("Docling processor initialized successfully!")