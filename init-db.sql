-- Inicialización de la base de datos para NotebookLlama Enhanced
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Habilitar la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear esquema para la aplicación
CREATE SCHEMA IF NOT EXISTS notebookllama;

-- Crear índices para mejor rendimiento
-- Los índices específicos se crearán cuando las tablas sean generadas por SQLAlchemy

-- Configuraciones de rendimiento
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- Configuraciones específicas para pgvector
ALTER SYSTEM SET 'vector.enable_prefilter' = 'on';

-- Crear usuario de aplicación (opcional, para mayor seguridad)
-- CREATE USER notebookllama_app WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE notebookllama_enhanced TO notebookllama_app;
-- GRANT ALL PRIVILEGES ON SCHEMA notebookllama TO notebookllama_app;

-- Función para limpiar datos antiguos (opcional)
CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS void AS $$
BEGIN
    -- Limpiar trazas antiguas (más de 30 días)
    DELETE FROM enhanced_agent_traces WHERE created_at < NOW() - INTERVAL '30 days';
    
    -- Limpiar chunks huérfanos
    DELETE FROM document_chunks 
    WHERE document_id NOT IN (SELECT id FROM documents_enhanced);
    
    RAISE NOTICE 'Cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Programar limpieza automática (opcional)
-- SELECT cron.schedule('cleanup-job', '0 2 * * *', 'SELECT cleanup_old_data();');
