# 🦙 NotebookLlama Enhanced

> Una versión mejorada de NotebookLM usando **Docling** para procesamiento de documentos y **PostgreSQL** para almacenamiento y búsqueda vectorial.

## ✨ Nuevas Características

### 🚀 Procesamiento Avanzado con Docling
- **Análisis de layout inteligente**: Reconocimiento superior de estructura de documentos
- **Extracción de tablas mejorada**: Usando el modelo TableFormer de IBM
- **OCR avanzado**: Soporte para documentos escaneados con múltiples motores
- **Procesamiento local**: Sin dependencias de APIs externas costosas
- **Múltiples formatos**: PDF, DOCX, PPTX, XLSX, HTML, imágenes

### 🐘 Base de Datos PostgreSQL Mejorada
- **Búsqueda vectorial**: Usando pgvector para búsquedas semánticas
- **Almacenamiento escalable**: Mejor rendimiento que SQLite
- **Embeddings locales**: Almacenamiento de vectores para búsqueda rápida
- **Metadatos enriquecidos**: Información detallada de procesamiento

### 🔗 Interfaz de Chat Personalizada
- **Conexión a APIs externas**: OpenAI, Anthropic, APIs locales
- **Configuración flexible**: Headers, autenticación, formatos de mensaje
- **Interfaz intuitiva**: Chat en tiempo real con cualquier servicio
- **Presets incluidos**: Configuraciones para APIs populares

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  Docling Core   │    │  PostgreSQL     │
│                 │◄──►│                 │◄──►│                 │
│ - Home          │    │ - PDF Parsing   │    │ - Documents     │
│ - Chat API      │    │ - Table Extract │    │ - Embeddings    │
│ - Management    │    │ - Image Process │    │ - Vector Search │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Audio Gen     │    │  Mind Maps      │    │   Observability │
│                 │    │                 │    │                 │
│ - ElevenLabs    │    │ - PyVis         │    │ - Jaeger        │
│ - Multi Voice   │    │ - Interactive   │    │ - Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Requisitos Previos

### Sistema
- Python 3.13+
- PostgreSQL 15+ con extensión pgvector
- Docker (opcional para servicios)

### APIs Requeridas
- **OpenAI API**: Para LLM y embeddings
- **ElevenLabs API**: Para generación de podcasts (opcional)

## 🚀 Instalación

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd notebookllama_improved
```

### 2. Configurar Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
# o usando el proyecto toml
pip install -e .
```

### 4. Configurar PostgreSQL

#### Opción A: Docker (Recomendado)
```bash
# Usar el compose.yaml incluido
docker-compose up -d postgres
```

#### Opción B: Instalación Local
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Crear base de datos
sudo -u postgres createdb notebookllama_enhanced

# Instalar pgvector
sudo apt install postgresql-15-pgvector
```

### 5. Configurar Variables de Entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

Ejemplo de `.env`:
```bash
OPENAI_API_KEY="sk-tu-clave-aqui"
ELEVENLABS_API_KEY="sk-tu-clave-aqui"

pgql_db="notebookllama_enhanced"
pgql_user="postgres"
pgql_psw="admin"
pgql_host="localhost"
pgql_port="5432"
```

### 6. Inicializar Base de Datos
```python
# Ejecutar una vez para crear tablas
python -c "
from src.notebookllama.postgres_manager import DOCUMENT_MANAGER
print('Base de datos inicializada correctamente')
"
```

## 🎯 Uso

### Iniciar la Aplicación
```bash
# Desde el directorio raíz
streamlit run src/notebookllama/Enhanced_Home.py

# La aplicación estará disponible en http://localhost:8501
```

### Servicios Opcionales

#### Servidor MCP Mejorado
```bash
# En terminal separada
cd src/notebookllama
python enhanced_server.py
```

#### Observabilidad (Jaeger)
```bash
# Usar Docker Compose
docker-compose up -d jaeger

# Jaeger UI disponible en http://localhost:16686
```

## 📖 Guía de Uso

### 1. Procesamiento de Documentos

1. **Subir Archivo**: Arrastra un PDF a la interfaz
2. **Configurar Título**: Asigna un nombre descriptivo
3. **Procesar**: Haz clic en "🚀 Process Document with Docling"
4. **Revisar Resultados**: 
   - Resumen automático
   - Puntos clave extraídos
   - Q&A generado
   - Mapa mental interactivo

### 2. Generación de Podcasts

1. **Procesar Documento**: Primero procesa tu contenido
2. **Configurar Podcast**: 
   - Estilo de conversación
   - Audiencia objetivo
   - Roles de los hablantes
   - Temas específicos
3. **Generar**: Crea tu podcast con IA
4. **Descargar**: Guarda el archivo MP3

### 3. Chat con API Personalizada

1. **Ir a "Custom Chat API"**: Navega a la nueva página
2. **Configurar Conexión**:
   ```
   API URL: https://api.openai.com/v1
   Endpoint: chat/completions
   Headers: Authorization: Bearer tu-api-key
   ```
3. **Formato de Mensaje**: Usa presets o configuración personalizada
4. **Conectar y Chatear**: Interactúa con cualquier API compatible

### 4. Gestión de Documentos

- **Ver Colección**: Página "Document Management"
- **Buscar Contenido**: Búsqueda semántica avanzada
- **Exportar Datos**: Funcionalidad de exportación
- **Métricas**: Estadísticas de la colección

## 🔧 Configuración Avanzada

### Docling Personalizado
```python
# En docling_processor.py
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True
```

### PostgreSQL Optimización
```sql
-- Configuraciones recomendadas para PostgreSQL
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements,pgvector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET effective_cache_size = '4GB';
```

### Embeddings Personalizados
```python
# Cambiar modelo de embeddings
embedding_model = OpenAIEmbedding(
    model="text-embedding-3-large",  # Mejor calidad
    api_key=os.getenv("OPENAI_API_KEY")
)
```

## 🔌 Integraciones de APIs

### APIs Compatibles

#### OpenAI
```json
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "{{message}}"}]
}
```

#### Anthropic Claude
```json
{
  "model": "claude-3-sonnet-20240229",
  "max_tokens": 1000,
  "messages": [{"role": "user", "content": "{{message}}"}]
}
```

#### APIs Locales (Ollama)
```json
{
  "model": "llama2",
  "prompt": "{{message}}",
  "stream": false
}
```

### Configuración de Headers
- **Bearer Token**: `Authorization: Bearer tu-token`
- **API Key**: `X-API-Key: tu-clave`
- **Custom**: Cualquier header personalizado

## 📊 Observabilidad

### Métricas Disponibles
- Tiempo de procesamiento por documento
- Uso de embeddings y vectores
- Estadísticas de API calls
- Rendimiento de consultas

### Jaeger Tracing
- Trazas distribuidas de workflows
- Análisis de performance
- Debugging de problemas

### Dashboard PostgreSQL
- Adminer incluido en `http://localhost:8080`
- Queries SQL personalizadas
- Visualización de datos

## 🐛 Solución de Problemas

### Problemas Comunes

#### Error de Conexión PostgreSQL
```bash
# Verificar que PostgreSQL esté ejecutándose
sudo systemctl status postgresql

# Revisar logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Docling No Procesa PDFs
```python
# Verificar instalación
python -c "from docling.document_converter import DocumentConverter; print('OK')"

# Revisar permisos de archivos
ls -la uploaded_file.pdf
```

#### APIs Externas Fallan
- Verificar URLs y endpoints
- Comprobar autenticación
- Revisar formato de mensaje
- Test de conectividad

### Logs de Debug
```bash
# Activar logs detallados
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# tu código aquí
"
```

## 📈 Rendimiento

### Optimizaciones Incluidas

#### Docling
- Procesamiento paralelo de páginas
- Cache de modelos AI
- Optimización de memoria

#### PostgreSQL
- Índices en campos críticos
- Configuración de pgvector
- Connection pooling

#### Streamlit
- Cache de resultados
- Lazy loading de componentes
- Optimización de sesiones

### Benchmarks
- **Procesamiento PDF**: ~2-5 segundos por página
- **Generación Embeddings**: ~0.1 segundos por chunk
- **Búsqueda Vectorial**: <100ms para consultas
- **Generación Podcast**: ~30 segundos por minuto

## 🛡️ Seguridad

### Mejores Prácticas
- Variables de entorno para credenciales
- Validación de entrada de archivos
- Sanitización de queries SQL
- Rate limiting en APIs

### Configuración PostgreSQL
```sql
-- Crear usuario específico
CREATE USER notebookllama WITH PASSWORD 'password-seguro';
GRANT CONNECT ON DATABASE notebookllama_enhanced TO notebookllama;
GRANT USAGE ON SCHEMA public TO notebookllama;
```

## 🚀 Desarrollo

### Estructura del Proyecto
```
src/notebookllama/
├── Enhanced_Home.py           # Página principal mejorada
├── docling_processor.py       # Procesador Docling
├── postgres_manager.py        # Gestor PostgreSQL
├── enhanced_workflow.py       # Workflow mejorado
├── enhanced_querying.py       # Sistema de consultas
├── enhanced_server.py         # Servidor MCP
├── pages/
│   ├── 5_Custom_Chat_API.py  # Nueva página de chat
│   └── ...                   # Otras páginas
├── models.py                  # Modelos de datos
├── audio.py                   # Generación de audio
├── mindmap.py                 # Mapas mentales
└── instrumentation.py        # Observabilidad
```

### Contribuir
1. Fork el repositorio
2. Crear feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Testing
```bash
# Ejecutar tests
pytest src/tests/

# Coverage
pytest --cov=src/notebookllama

# Linting
flake8 src/
mypy src/
```

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Áreas de enfoque:
- Nuevos conectores de APIs
- Mejoras en procesamiento Docling
- Optimizaciones de PostgreSQL
- Funciones de visualización
- Tests automatizados

## 📞 Soporte

- **Issues**: Reportar en GitHub Issues
- **Discusiones**: GitHub Discussions
- **Documentación**: Wiki del repositorio

---

## 🆚 Comparación con Versión Original

| Característica | Original | Enhanced |
|----------------|----------|----------|
| **Procesamiento** | LlamaCloud | Docling (Local) |
| **Base de Datos** | SQLite | PostgreSQL + pgvector |
| **Búsqueda** | Básica | Vectorial semántica |
| **APIs** | Fijo | Configurables |
| **Escalabilidad** | Limitada | Alta |
| **Costos** | API costs | Solo OpenAI |
| **Privacidad** | Depende API | Local completo |

---

¡Disfruta de la versión mejorada de NotebookLlama! 🦙✨
