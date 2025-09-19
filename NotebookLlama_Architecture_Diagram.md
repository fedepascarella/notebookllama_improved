# NotebookLlama Enhanced - Complete Architecture Sequence Diagram

## Overview
This diagram shows the complete flow of the NotebookLlama Enhanced system, from document upload through processing, storage, and various output generation capabilities.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI<br/>(Enhanced_Home.py)
    participant WF as Enhanced Workflow<br/>(enhanced_workflow.py)
    participant DP as Docling Processor<br/>(docling_processor.py)
    participant DC as DocumentConverter<br/>(Docling Core)
    participant LLM as OpenAI LLM<br/>(GPT-4)
    participant PG as PostgreSQL Manager<br/>(postgres_manager.py)
    participant DB as PostgreSQL<br/>(+ pgvector)
    participant EQ as Enhanced Query<br/>(enhanced_querying.py)
    participant AG as Audio Generator<br/>(audio.py)
    participant EL as ElevenLabs API
    participant MM as Mind Map<br/>(mindmap.py)
    participant CA as Custom Chat API<br/>(5_Custom_Chat_API.py)
    participant ES as Enhanced Server<br/>(enhanced_server.py)
    participant OT as Observability<br/>(instrumentation.py)

    Note over User,OT: Document Processing Flow

    User->>UI: Upload PDF Document
    UI->>UI: Create temp file
    UI->>WF: Run Enhanced Workflow
    activate WF

    WF->>WF: Create StartEvent with file info
    WF->>DP: Process document
    activate DP

    DP->>DC: Convert document
    DC->>DC: Parse PDF structure
    DC->>DC: Extract tables (TableFormer)
    DC->>DC: OCR if needed
    DC-->>DP: Return structured data

    DP->>LLM: Generate notebook content
    LLM->>LLM: Create summary
    LLM->>LLM: Generate Q&A pairs
    LLM->>LLM: Extract key points
    LLM-->>DP: Return notebook

    DP-->>WF: ProcessedDocument
    deactivate DP

    WF->>PG: Store document
    activate PG
    PG->>PG: Generate embeddings
    PG->>DB: Save document record
    DB-->>PG: Document ID

    PG->>PG: Chunk document
    PG->>PG: Generate chunk embeddings
    PG->>DB: Save chunks with vectors
    DB-->>PG: Chunk IDs

    PG->>DB: Update vector index
    PG-->>WF: Storage complete
    deactivate PG

    WF->>MM: Generate mind map
    MM->>MM: Extract concepts
    MM->>MM: Build graph structure
    MM->>MM: Create PyVis visualization
    MM-->>WF: HTML mind map

    WF-->>UI: Return results dictionary
    deactivate WF

    UI->>UI: Display results
    UI-->>User: Show processed document

    Note over User,OT: Podcast Generation Flow

    User->>UI: Request podcast generation
    UI->>AG: Initialize PodcastGenerator
    activate AG

    AG->>AG: Configure voices & style
    AG->>LLM: Generate conversation script
    LLM->>LLM: Create multi-turn dialogue
    LLM-->>AG: Return conversation turns

    loop For each conversation turn
        AG->>EL: Generate audio (speaker voice)
        EL-->>AG: Audio chunk
        AG->>AG: Store audio segment
    end

    AG->>AG: Merge audio segments
    AG->>AG: Apply audio processing
    AG-->>UI: Return podcast MP3
    deactivate AG

    UI-->>User: Download podcast

    Note over User,OT: Document Query Flow

    User->>UI: Enter search query
    UI->>EQ: Search documents
    activate EQ

    EQ->>PG: Vector similarity search
    PG->>DB: Query pgvector index
    DB-->>PG: Similar chunks
    PG-->>EQ: Relevant documents

    EQ->>LLM: Generate response with citations
    LLM-->>EQ: Formatted answer
    EQ-->>UI: Search results
    deactivate EQ

    UI-->>User: Display results

    Note over User,OT: Custom API Chat Flow

    User->>CA: Configure API endpoint
    CA->>CA: Validate URL & headers
    CA->>CA: Test connection

    User->>CA: Send chat message
    activate CA
    CA->>CA: Format message per API spec
    CA->>External API: POST request
    External API-->>CA: Response
    CA->>CA: Parse response
    CA-->>User: Display message
    deactivate CA

    Note over User,OT: MCP Server Flow (Optional)

    User->>ES: Start MCP server
    activate ES
    ES->>ES: Initialize FastAPI
    ES->>PG: Connect to database

    loop Handle requests
        External->>ES: API request
        ES->>PG: Query/Update data
        PG->>DB: Database operations
        DB-->>PG: Results
        PG-->>ES: Data
        ES-->>External: Response
    end
    deactivate ES

    Note over User,OT: Observability Flow (Optional)

    par Parallel Tracing
        WF->>OT: Send trace data
        and
        PG->>OT: Send query metrics
        and
        AG->>OT: Send generation metrics
    end

    OT->>OT: Aggregate traces
    OT->>Jaeger: Export spans
    Jaeger-->>Admin: View traces
```

## Component Descriptions

### Core Components

1. **Streamlit UI (Enhanced_Home.py)**
   - Main user interface
   - Handles file uploads
   - Displays results and visualizations
   - Manages user sessions

2. **Enhanced Workflow (enhanced_workflow.py)**
   - Orchestrates document processing pipeline
   - Manages event flow between components
   - Handles error recovery

3. **Docling Processor (docling_processor.py)**
   - Local document parsing (no external APIs)
   - Advanced table extraction
   - OCR capabilities
   - Structured data extraction

4. **PostgreSQL Manager (postgres_manager.py)**
   - Document storage and retrieval
   - Vector embeddings management
   - Semantic search using pgvector
   - Metadata handling

### AI Components

5. **OpenAI LLM Integration**
   - Summary generation
   - Q&A creation
   - Conversation script generation
   - Response formatting

6. **Audio Generator (audio.py)**
   - Podcast script creation
   - Multi-voice synthesis via ElevenLabs
   - Audio merging and processing
   - MP3 generation

### Utility Components

7. **Mind Map Generator (mindmap.py)**
   - Concept extraction
   - Interactive graph visualization
   - PyVis integration

8. **Custom Chat API (5_Custom_Chat_API.py)**
   - External API connectivity
   - Flexible message formatting
   - Support for various LLM providers

9. **Enhanced Server (enhanced_server.py)**
   - MCP protocol implementation
   - FastAPI server
   - REST API endpoints

10. **Instrumentation (instrumentation.py)**
    - OpenTelemetry tracing
    - Performance metrics
    - Jaeger integration

## Data Flow Summary

1. **Input**: User uploads PDF document
2. **Processing**: Docling extracts content, tables, and structure
3. **Enhancement**: LLM generates summaries, Q&A, and insights
4. **Storage**: PostgreSQL stores documents with vector embeddings
5. **Outputs**:
   - Interactive notebook view
   - Mind map visualization
   - Podcast audio generation
   - Semantic search capabilities
   - Custom API chat interface

## Key Features

- **Local Processing**: No dependency on external document processing APIs
- **Vector Search**: Semantic search using pgvector
- **Scalability**: PostgreSQL for better performance than SQLite
- **Flexibility**: Connect to any LLM API
- **Observability**: Built-in tracing and metrics
- **Multi-modal**: Text, audio, and visual outputs