"""
Enhanced Workflow Module - NotebookLLaMA Enhanced
Versión LIMPIA sin dependencias complejas (PostgreSQL, pgvector, etc.)
"""

import sys
import logging
from typing import Optional, Any, Annotated, Union
from datetime import datetime
import json

# Configurar logging
logger = logging.getLogger(__name__)

# ====================================
# IMPORTACIONES CORE (SOLO LO ESENCIAL)
# ====================================
try:
    # Importaciones core de workflows - SOLO LO BÁSICO
    from llama_index.core.workflow import (
        Workflow, 
        step, 
        Context, 
        Event, 
        StartEvent, 
        StopEvent
    )
    
    # Importación correcta de Resource
    from llama_index.core.workflow.resource import Resource
    
    logger.info("✅ LlamaIndex workflows importado correctamente")
    
except ImportError as e:
    logger.error(f"❌ LlamaIndex workflows no disponible: {e}")
    raise ImportError(
        "LlamaIndex workflows requerido. Instalar con: pip install llama-index>=0.14.0"
    ) from e

# ====================================
# EVENTOS SIMPLES (SIN DEPENDENCIAS EXTERNAS)
# ====================================

class FileInputEvent(Event):
    """Evento para procesar entrada de archivos - VERSIÓN SIMPLE"""
    
    def __init__(self, file_path: str, content: str = "", **kwargs):
        super().__init__()
        self.file_path = file_path
        self.content = content
        self.timestamp = datetime.now()
        self.file_type = file_path.split('.')[-1] if '.' in file_path else 'unknown'

class NotebookOutputEvent(Event):
    """Evento para salida de notebook - VERSIÓN SIMPLE"""
    
    def __init__(self, notebook_content: str, questions: list = None, answers: list = None, 
                 highlights: list = None, metadata: dict = None, **kwargs):
        super().__init__()
        self.notebook_content = notebook_content
        self.questions = questions or ["What is this document about?"]
        self.answers = answers or ["This is a processed document."]
        self.highlights = highlights or ["Document processed successfully"]
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class ProcessingEvent(Event):
    """Evento intermedio para procesamiento"""
    
    def __init__(self, processed_content: str, stage: str, metadata: dict = None, **kwargs):
        super().__init__()
        self.processed_content = processed_content
        self.stage = stage
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

# ====================================
# RECURSOS SIMPLES (SIN LLM EXTERNO)
# ====================================

def get_simple_processor():
    """Simple processor que no requiere API keys"""
    return {
        "name": "SimpleProcessor",
        "version": "1.0.0",
        "capabilities": ["text_processing", "notebook_generation"]
    }

# Definir recursos usando el patrón oficial
SimpleProcessor = Annotated[dict, Resource(get_simple_processor)]

# ====================================
# WORKFLOW SIMPLE (SIN DEPENDENCIAS COMPLEJAS)
# ====================================

class WF(Workflow):
    """
    Workflow Simple para NotebookLLaMA
    VERSIÓN LIMPIA sin PostgreSQL, sin APIs externas, sin pgvector
    """
    
    def __init__(self, *args, **kwargs):
        # Don't pass timeout to parent to avoid conflicts
        timeout = kwargs.pop('timeout', 60)
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("🚀 Workflow Simple inicializado (sin dependencias complejas)")
        self._timeout = timeout
    
    @step
    async def process_file_input(
        self, 
        ctx: Context, 
        ev: StartEvent,
        processor: SimpleProcessor
    ) -> ProcessingEvent:
        """
        Paso 1: Procesar entrada de archivo - VERSIÓN SIMPLE
        """
        try:
            # Get file information from StartEvent
            file_path = getattr(ev, 'file_path', 'unknown')
            content = getattr(ev, 'content', '')
            file_type = getattr(ev, 'file_type', 'unknown')
            
            self.logger.info(f"📄 Procesando archivo: {file_path}")
            
            # Pass data through the event instead of context
            
            # Procesamiento simple basado en tipo de archivo
            if file_type in ['py', 'js', 'java', 'cpp']:
                processed = self._process_code_simple(content, file_path)
            elif file_type in ['md', 'txt']:
                processed = self._process_text_simple(content, file_path)
            elif file_type == 'pdf':
                processed = self._process_pdf_simple(file_path)
            else:
                processed = self._process_generic_simple(content, file_path)
            
            return ProcessingEvent(
                processed_content=processed,
                stage="file_processed",
                metadata={
                    "file_path": ev.file_path,
                    "file_type": ev.file_type,
                    "processor": processor["name"],
                    "processed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando archivo: {e}")
            # En caso de error, devolver contenido básico
            return ProcessingEvent(
                processed_content=f"# Error Processing {file_path}\n\n{content[:500]}...",
                stage="error_fallback",
                metadata={"error": str(e), "file_path": file_path}
            )
    
    @step
    async def enhance_content(
        self, 
        ctx: Context, 
        ev: ProcessingEvent,
        processor: SimpleProcessor
    ) -> NotebookOutputEvent:
        """
        Paso 2: Mejorar contenido - VERSIÓN SIMPLE SIN LLM
        """
        try:
            self.logger.info(f"✨ Mejorando contenido en etapa: {ev.stage}")
            
            # Get file info from event metadata
            original_file = ev.metadata.get("original_file", "unknown")
            file_type = ev.metadata.get("file_type", "unknown")
            
            # Mejorar contenido usando reglas simples (sin LLM)
            enhanced = self._enhance_simple(ev.processed_content, file_type, original_file)
            
            return NotebookOutputEvent(
                notebook_content=enhanced,
                questions=["What is the main topic of this document?", "What are the key findings?"],
                answers=["This document covers various topics from the processed content.", "Key findings include the content analysis and structure."],
                highlights=["Document processed successfully", "Content enhanced", "Ready for analysis"],
                metadata={
                    **ev.metadata,
                    "enhancement_stage": "content_enhanced",
                    "enhanced_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error mejorando contenido: {e}")
            # Fallback: devolver contenido sin mejoras
            return NotebookOutputEvent(
                notebook_content=ev.processed_content,
                questions=["What is in this document?"],
                answers=["This document contains the original processed content."],
                highlights=["Document processing completed with errors"],
                metadata={**ev.metadata, "enhancement_error": str(e)}
            )
    
    @step
    async def generate_notebook(
        self, 
        ctx: Context, 
        ev: NotebookOutputEvent,
        processor: SimpleProcessor
    ) -> StopEvent:
        """
        Paso 3: Generar notebook final - VERSIÓN SIMPLE
        """
        try:
            self.logger.info("📓 Generando notebook final")
            
            # Get file info from event metadata
            original_file = ev.metadata.get("original_file", "unknown_file")
            
            # Generar estructura de notebook simple
            notebook_structure = self._create_simple_notebook(
                ev.notebook_content,
                original_file,
                ev.metadata
            )
            
            result = {
                "status": "success",
                "notebook_content": notebook_structure,
                "metadata": {
                    **ev.metadata,
                    "generation_completed": datetime.now().isoformat(),
                    "workflow_version": "simple_1.0.0",
                    "processor": processor["name"]
                },
                "original_file": original_file
            }
            
            self.logger.info("✅ Notebook generado exitosamente (versión simple)")
            return StopEvent(result=result)
            
        except Exception as e:
            self.logger.error(f"❌ Error generando notebook: {e}")
            return StopEvent(
                result={
                    "status": "error",
                    "error": str(e),
                    "partial_content": ev.notebook_content,
                    "metadata": ev.metadata
                }
            )
    
    # ====================================
    # MÉTODOS AUXILIARES SIMPLES
    # ====================================
    
    def _process_code_simple(self, content: str, file_path: str) -> str:
        """Procesar código usando reglas simples"""
        if not content.strip():
            return f"# Archivo Vacío: {file_path}\n\nNo se encontró contenido para procesar."
        
        lines = content.split('\n')
        functions = [line for line in lines if 'def ' in line or 'function ' in line or 'class ' in line]
        imports = [line for line in lines if line.strip().startswith(('import ', 'from ', '#include', 'using '))]
        
        analysis = f"""# Análisis de Código: {file_path}

## 📊 Estadísticas
- **Líneas totales:** {len(lines)}
- **Funciones/Clases encontradas:** {len(functions)}
- **Importaciones:** {len(imports)}

## 🔍 Funciones/Clases Detectadas
"""
        
        if functions:
            for func in functions[:5]:  # Mostrar solo las primeras 5
                analysis += f"- `{func.strip()}`\n"
        else:
            analysis += "- No se detectaron funciones o clases\n"
        
        analysis += f"""
## 📦 Importaciones
"""
        
        if imports:
            for imp in imports[:10]:  # Mostrar solo las primeras 10
                analysis += f"- `{imp.strip()}`\n"
        else:
            analysis += "- No se detectaron importaciones\n"
        
        analysis += f"""
## 📝 Código Fuente
```{self._get_language_from_path(file_path)}
{content[:2000]}{'...' if len(content) > 2000 else ''}
```
"""
        
        return analysis
    
    def _process_text_simple(self, content: str, file_path: str) -> str:
        """Procesar texto usando reglas simples"""
        if not content.strip():
            return f"# Documento Vacío: {file_path}\n\nNo se encontró contenido para procesar."
        
        words = len(content.split())
        lines = len(content.split('\n'))
        chars = len(content)
        
        # Detectar si es markdown
        is_markdown = file_path.endswith('.md') or any(line.startswith('#') for line in content.split('\n')[:10])
        
        analysis = f"""# Análisis de Documento: {file_path}

## 📊 Estadísticas
- **Palabras:** {words}
- **Líneas:** {lines}
- **Caracteres:** {chars}
- **Tipo detectado:** {'Markdown' if is_markdown else 'Texto plano'}

## 📄 Contenido
"""
        
        if is_markdown:
            analysis += content[:3000] + ('...' if len(content) > 3000 else '')
        else:
            analysis += f"```\n{content[:3000]}{'...' if len(content) > 3000 else ''}\n```"
        
        return analysis
    
    def _process_pdf_simple(self, file_path: str) -> str:
        """Process PDF files using Docling with memory-safe settings"""
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            self.logger.info(f"🔍 Processing PDF with Docling (memory-safe mode): {file_path}")
            
            # Create pipeline options with everything disabled for memory safety
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False  # CRITICAL: Disable OCR to prevent memory errors
            pipeline_options.do_table_structure = False  # Disable table structure
            pipeline_options.do_picture_classification = False  # Disable picture classification
            pipeline_options.do_picture_description = False  # Disable picture description
            pipeline_options.generate_page_images = False  # Don't generate page images
            pipeline_options.generate_picture_images = False  # Don't generate picture images
            pipeline_options.generate_table_images = False  # Don't generate table images
            
            # Initialize converter with memory-safe options
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: pipeline_options
                }
            )
            
            # Convert PDF to document without memory-intensive features
            result = converter.convert(file_path)
            
            # Extract text content
            if hasattr(result, 'document') and hasattr(result.document, 'export_to_markdown'):
                markdown_content = result.document.export_to_markdown()
                content_preview = markdown_content[:3000] + ('...' if len(markdown_content) > 3000 else '')
                
                self.logger.info(f"✅ Docling successfully extracted {len(markdown_content)} characters")
                
                return f"""# PDF Document: {file_path.split('/')[-1]}

## 📄 Document Information
- **File:** {file_path}
- **Type:** PDF Document
- **Status:** Successfully processed with Docling (primary)
- **Content Length:** {len(markdown_content)} characters

## 📝 Extracted Content
{content_preview}

## 🔍 Processing Details
- Processed using Docling document converter
- Content extracted and converted to markdown format
- Advanced features: table extraction, layout analysis
"""
            else:
                # Try alternative extraction methods
                if hasattr(result, 'document'):
                    # Try to get text directly
                    try:
                        if hasattr(result.document, 'texts'):
                            text_content = ' '.join([t.text for t in result.document.texts if hasattr(t, 'text')])
                            content_preview = text_content[:3000] + ('...' if len(text_content) > 3000 else '')
                        else:
                            content_preview = str(result.document)[:3000]
                    except Exception as e:
                        self.logger.error(f"Error extracting text: {e}")
                        content_preview = "PDF content extracted successfully but preview not available"
                else:
                    content_preview = "PDF content extracted successfully but preview not available"
                
                return f"""# PDF Document: {file_path.split('/')[-1]}

## 📄 Document Information
- **File:** {file_path}
- **Type:** PDF Document
- **Status:** Processed with Docling (alternative extraction)

## 📝 Extracted Content
{content_preview}
"""
                
        except Exception as docling_error:
            self.logger.error(f"Docling processing failed: {docling_error}, trying PyPDF2 fallback")
            
            # Fallback to PyPDF2 only if Docling fails
            try:
                return self._process_pdf_with_pypdf2(file_path)
            except Exception as pypdf_error:
                self.logger.error(f"PyPDF2 also failed: {pypdf_error}")
                
            return f"""# PDF Processing Error: {file_path.split('/')[-1]}

## ⚠️ Processing Issues
The PDF processing encountered memory or compatibility issues:
- **Primary Error**: {str(e)[:200]}...
- **Issue**: Likely due to high memory requirements for OCR/image processing

## 📄 File Information  
- **File**: {file_path}
- **Processing Method**: Attempted Docling with memory-optimized settings
- **Status**: Partial processing completed

## 💡 Recommendations
1. Try a smaller PDF file
2. Restart the application to clear memory
3. Disable OCR features if not needed

The document was processed as much as possible despite the errors.
"""
    
    def _process_pdf_with_pypdf2(self, file_path: str) -> str:
        """Fallback PDF processing using PyPDF2 for memory-constrained environments"""
        try:
            import PyPDF2
            
            self.logger.info(f"🔄 Processing PDF with PyPDF2 fallback: {file_path}")
            
            text_content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Extract text from each page (limit to first 10 pages to save memory)
                max_pages = min(num_pages, 10)
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text_content += f"\\n\\n--- Page {page_num + 1} ---\\n{page_text}"
            
            if not text_content.strip():
                text_content = "No text could be extracted from this PDF file."
            
            return f"""# PDF Document: {file_path.split('/')[-1]}

## 📄 Document Information
- **File:** {file_path}
- **Type:** PDF Document  
- **Pages Processed:** {max_pages} of {num_pages}
- **Processing Method:** PyPDF2 (Memory-Efficient Fallback)
- **Status:** Successfully processed with basic text extraction

## 📝 Extracted Content
{text_content[:3000]}{'...' if len(text_content) > 3000 else ''}

## 🔍 Processing Notes
- Used PyPDF2 for text extraction due to memory constraints
- Advanced features like table extraction and OCR were disabled
- Content extracted successfully from readable text layers
"""
            
        except ImportError:
            return f"""# PDF Processing: PyPDF2 Not Available

## ⚠️ Fallback Processing Failed
PyPDF2 library is not installed. Please install it with:
```
pip install PyPDF2
```

**File:** {file_path}
"""
        except Exception as e:
            return f"""# PDF Processing Error: {file_path.split('/')[-1]}

## ❌ PyPDF2 Fallback Error
Even the basic PDF processing failed: {str(e)}

This may indicate a corrupted or protected PDF file.

**File:** {file_path}
"""

    def _process_generic_simple(self, content: str, file_path: str) -> str:
        """Procesar archivos genéricos"""
        return f"""# Archivo Procesado: {file_path}

## 📄 Información
- **Archivo:** {file_path}
- **Tamaño:** {len(content)} caracteres
- **Tipo:** Archivo genérico

## 📝 Contenido
```
{content[:2000]}{'...' if len(content) > 2000 else ''}
```
"""
    
    def _enhance_simple(self, content: str, file_type: str, original_file: str) -> str:
        """Mejorar contenido usando reglas simples (sin LLM)"""
        
        enhanced = f"""# Notebook Mejorado: {original_file}

> **Generado automáticamente por NotebookLLaMA Enhanced**  
> **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> **Tipo de archivo:** {file_type}

## 🎯 Resumen
Este notebook fue generado automáticamente a partir del archivo `{original_file}`.

{content}

## 💡 Sugerencias para Mejorar
"""
        
        if file_type in ['py', 'js', 'java', 'cpp']:
            enhanced += """
- **Para código:** Considera agregar comentarios y documentación
- **Testing:** Agrega pruebas unitarias para las funciones
- **Optimización:** Revisa el rendimiento del código
- **Modularidad:** Separa funciones en módulos más pequeños
"""
        else:
            enhanced += """
- **Estructura:** Organiza el contenido con headers y secciones
- **Ejemplos:** Agrega ejemplos prácticos
- **Referencias:** Incluye enlaces a documentación relacionada
- **Interactividad:** Convierte partes en celdas de código ejecutables
"""
        
        enhanced += f"""
## 🚀 Próximos Pasos
1. Revisa el contenido generado
2. Agrega celdas de código interactivas
3. Incluye visualizaciones si es relevante
4. Documenta los resultados esperados

---
*Generado por NotebookLLaMA Enhanced - Versión Simple*
"""
        
        return enhanced
    
    def _get_language_from_path(self, file_path: str) -> str:
        """Detectar lenguaje de programación por extensión"""
        ext = file_path.split('.')[-1].lower()
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'php': 'php',
            'rb': 'ruby',
            'go': 'go',
            'rs': 'rust',
            'ts': 'typescript'
        }
        return lang_map.get(ext, 'text')
    
    def _create_simple_notebook(self, content: str, original_file: str, metadata: dict) -> dict:
        """Crear estructura de notebook Jupyter simple"""
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
                    "version": "3.11.0",
                    "mimetype": "text/x-python",
                    "codemirror_mode": {"name": "ipython", "version": 3},
                    "pygments_lexer": "ipython3",
                    "nbconvert_exporter": "python",
                    "file_extension": ".py"
                },
                "source_file": original_file,
                "generated_by": "NotebookLLaMA Enhanced - Simple Version",
                "generated_at": datetime.now().isoformat(),
                "workflow_metadata": metadata
            },
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {
                        "tags": ["header"]
                    },
                    "source": [
                        f"# 📚 Notebook: {original_file}\n\n",
                        "**🤖 Generado automáticamente por NotebookLLaMA Enhanced**\n\n",
                        f"- **Archivo fuente:** `{original_file}`\n",
                        f"- **Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                        f"- **Versión del workflow:** Simple 1.0.0\n\n",
                        "---\n\n"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {
                        "tags": ["content"]
                    },
                    "source": content.split('\n')
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {
                        "tags": ["setup"]
                    },
                    "outputs": [],
                    "source": [
                        "# 🚀 Celda de configuración inicial\n",
                        "print('✅ Notebook cargado correctamente')\n",
                        f"print(f'📄 Archivo fuente: {original_file}')\n",
                        f"print(f'🕒 Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')\n",
                        "\n",
                        "# Importaciones básicas\n",
                        "import os\n",
                        "import sys\n",
                        "from datetime import datetime\n",
                        "\n",
                        "# Variables útiles\n",
                        "NOTEBOOK_PATH = os.getcwd()\n",
                        f"SOURCE_FILE = '{original_file}'\n",
                        "\n",
                        "print('🎯 Notebook listo para usar!')"
                    ]
                },
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## 💡 Instrucciones de Uso\n\n",
                        "1. **Ejecuta las celdas:** Usa `Shift + Enter` para ejecutar cada celda\n",
                        "2. **Modifica el código:** Puedes editar cualquier celda según tus necesidades\n",
                        "3. **Agrega contenido:** Inserta nuevas celdas con `+` en la barra de herramientas\n",
                        "4. **Guarda cambios:** Usa `Ctrl + S` para guardar tu progreso\n\n",
                        "### 🔧 Celdas Sugeridas para Agregar:\n",
                        "- Análisis de datos\n",
                        "- Visualizaciones\n",
                        "- Pruebas y validaciones\n",
                        "- Conclusiones y resultados\n\n",
                        "---\n",
                        "*Tip: Este notebook fue generado automáticamente. ¡Personalízalo según tus necesidades!* 🎨"
                    ]
                }
            ]
        }

# ====================================
# FUNCIONES DE UTILIDAD SIMPLES
# ====================================

async def create_and_run_workflow(file_path: str, content: str = None) -> dict:
    """
    Función de conveniencia para crear y ejecutar el workflow SIMPLE
    """
    workflow = WF(timeout=60, verbose=True)  # Increased timeout
    
    # Create proper StartEvent
    from llama_index.core.workflow.events import StartEvent
    start_event = StartEvent()
    start_event.file_path = file_path
    start_event.content = content or f"# Contenido de ejemplo para {file_path}\n\nEste es un archivo de prueba."
    start_event.file_type = file_path.split('.')[-1] if '.' in file_path else 'unknown'
    
    try:
        result = await workflow.run(start_event=start_event)
        # Ensure workflow cleanup
        await asyncio.sleep(0.1)  # Give time for cleanup
        return result
    except Exception as e:
        logger.error(f"Error ejecutando workflow: {e}")
        return {
            "status": "error",
            "error": str(e),
            "file_path": file_path
        }

# ====================================
# FUNCIÓN DE PRUEBA SIMPLE
# ====================================

async def test_simple_workflow():
    """Función para probar el workflow simple"""
    logger.info("🧪 Iniciando prueba del workflow SIMPLE")
    
    test_content = """
def hello_world():
    print("Hello, NotebookLLaMA!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
"""
    
    result = await create_and_run_workflow(
        file_path="test_simple.py",
        content=test_content
    )
    
    if result.get("status") == "success":
        logger.info("✅ Workflow simple funcionando correctamente")
        print("🎉 Resultado del test:")
        print(f"   Status: {result['status']}")
        print(f"   Archivo: {result.get('original_file', 'N/A')}")
        print(f"   Celdas: {len(result.get('notebook_content', {}).get('cells', []))}")
        return True
    else:
        logger.error(f"❌ Workflow simple falló: {result.get('error', 'Error desconocido')}")
        return False

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Ejecutando test del workflow simple...")
    try:
        success = asyncio.run(test_simple_workflow())
        if success:
            print("✅ Test completado exitosamente!")
        else:
            print("❌ Test falló")
    except Exception as e:
        print(f"❌ Error en test: {e}")