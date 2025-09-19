# 🚀 NotebookLlama Enhanced - Complete Startup Guide

## Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **Python 3.11+**
- **Git** (for version control)

### Required API Keys
- **OpenAI API Key** - For LLM and embeddings
- **ElevenLabs API Key** - For podcast generation (optional)

## 📋 Step-by-Step Startup Instructions

### 1. Environment Setup

First, ensure your `.env` file is properly configured:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional (for podcast generation)
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# PostgreSQL Configuration (defaults are fine for local development)
pgql_db=notebookllama_enhanced
pgql_user=postgres
pgql_psw=admin
pgql_host=localhost
pgql_port=5432
```

### 2. Start Docker Services

Open a terminal in the project root directory and run:

```bash
# Start all services (PostgreSQL, Jaeger, Adminer, Redis)
docker-compose up -d

# Or start only essential services (PostgreSQL)
docker-compose up -d postgres

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                            STATUS      PORTS
notebookllama-enhanced-postgres-1   Up      0.0.0.0:5432->5432/tcp
notebookllama-enhanced-jaeger-1     Up      0.0.0.0:16686->16686/tcp, ...
notebookllama-enhanced-adminer-1    Up      0.0.0.0:8080->8080/tcp
notebookllama-enhanced-redis-1      Up      0.0.0.0:6379->6379/tcp
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install via pyproject.toml
pip install -e .
```

### 4. Initialize Database

The database is automatically initialized when Docker starts, but you can verify:

```bash
# Test database connection
python -c "
from src.notebookllama.postgres_manager import DOCUMENT_MANAGER
print('✅ Database connection successful!')
"
```

### 5. Start the Application

```bash
# Start Streamlit application
streamlit run src/notebookllama/Enhanced_Home.py

# The application will open at http://localhost:8501
```

### 6. Optional: Start Additional Services

#### MCP Server (for API access)
```bash
# In a new terminal
cd src/notebookllama
python enhanced_server.py
# Server will run on http://localhost:8000
```

## 🔧 Service URLs

Once everything is running, you can access:

- **Main Application**: http://localhost:8501
- **Adminer (Database UI)**: http://localhost:8080
  - System: PostgreSQL
  - Server: postgres
  - Username: postgres
  - Password: admin
  - Database: notebookllama_enhanced
- **Jaeger (Tracing)**: http://localhost:16686
- **MCP API Server**: http://localhost:8000 (if started)
- **Redis Commander** (if installed): http://localhost:8081

## 🛠️ Troubleshooting

### Docker Issues

#### Check if Docker is running:
```bash
docker version
```

#### If services fail to start:
```bash
# View logs
docker-compose logs postgres
docker-compose logs

# Restart services
docker-compose restart

# Complete reset (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

#### Check PostgreSQL is accessible:
```bash
# Test connection
docker exec -it notebookllama-enhanced-postgres-1 psql -U postgres -d notebookllama_enhanced -c "\dt"
```

#### Reset database:
```bash
# Stop services
docker-compose down

# Remove volume (deletes all data)
docker volume rm notebookllama_improved_pgdata

# Start fresh
docker-compose up -d postgres
```

### Python/Application Issues

#### Module not found errors:
```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### Port already in use:
```bash
# Find process using port 8501
# Windows:
netstat -ano | findstr :8501
# Linux/Mac:
lsof -i :8501

# Kill the process or use different port:
streamlit run src/notebookllama/Enhanced_Home.py --server.port 8502
```

## 📊 Verifying Everything Works

### 1. Check Docker Services
```bash
docker-compose ps
# All services should show "Up" status
```

### 2. Check Database
Open Adminer at http://localhost:8080 and verify you can login and see the database.

### 3. Check Application
1. Open http://localhost:8501
2. Upload a test PDF
3. Click "Process Document with Docling"
4. Verify processing completes successfully

### 4. Check Tracing (Optional)
Open Jaeger at http://localhost:16686 and look for traces from "enhanced.agent.traces"

## 🔄 Daily Operations

### Starting Everything
```bash
# Start Docker services
docker-compose up -d

# Activate Python environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start application
streamlit run src/notebookllama/Enhanced_Home.py
```

### Stopping Everything
```bash
# Stop application: Press Ctrl+C in terminal

# Stop Docker services (preserves data)
docker-compose stop

# Or completely shut down (preserves data)
docker-compose down

# Complete cleanup (WARNING: deletes all data)
docker-compose down -v
```

### Viewing Logs
```bash
# Docker service logs
docker-compose logs -f postgres
docker-compose logs -f jaeger

# Application logs
# These appear in the terminal where Streamlit is running
```

## 💾 Backup and Restore

### Backup Database
```bash
# Create backup
docker exec notebookllama-enhanced-postgres-1 pg_dump -U postgres notebookllama_enhanced > backup.sql

# Backup with timestamp
docker exec notebookllama-enhanced-postgres-1 pg_dump -U postgres notebookllama_enhanced > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
# Restore from backup
docker exec -i notebookllama-enhanced-postgres-1 psql -U postgres notebookllama_enhanced < backup.sql
```

## 🚨 Common Commands Reference

```bash
# Docker Commands
docker-compose up -d          # Start all services
docker-compose stop          # Stop all services
docker-compose restart       # Restart all services
docker-compose logs -f       # View logs (follow mode)
docker-compose ps           # List running services
docker-compose down         # Stop and remove containers
docker-compose down -v      # Stop, remove containers and volumes

# Application Commands
streamlit run src/notebookllama/Enhanced_Home.py  # Start main app
python enhanced_server.py                          # Start API server
python test_fixes.py                              # Run tests

# Database Commands
docker exec -it notebookllama-enhanced-postgres-1 psql -U postgres  # Access PostgreSQL
```

## 📝 Notes

- The first document processing might take longer as models are downloaded
- Ensure you have at least 4GB RAM available for Docker
- PostgreSQL data persists in Docker volumes between restarts
- Use Adminer for easy database management and queries
- Jaeger tracing is optional and can be disabled if not needed