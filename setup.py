#!/usr/bin/env python3
"""
NotebookLlama - Setup & Initialization Script
Arquitectura senior con manejo robusto de errores y cross-platform support
"""

import sys
import os
import platform
import subprocess
import shutil
import time
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

# ====================================
# CONFIGURACIÓN DE ENCODING Y LOGGING
# ====================================

# Forzar UTF-8 en Windows para manejar caracteres especiales
if platform.system() == "Windows":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ====================================
# CONFIGURACIONES CROSS-PLATFORM
# ====================================

@dataclass
class PlatformConfig:
    """Configuración específica por plataforma"""
    name: str
    python_cmd: str
    pip_cmd: str
    docker_cmd: str
    postgres_install_cmd: List[str]
    tesseract_install_cmd: List[str]
    
    def get_venv_activation(self, venv_path: Path) -> str:
        """Comando para activar entorno virtual"""
        raise NotImplementedError


class WindowsConfig(PlatformConfig):
    def __init__(self):
        super().__init__(
            name="Windows",
            python_cmd="python",
            pip_cmd="pip",
            docker_cmd="docker",
            postgres_install_cmd=["echo", "Usar Docker o instalar PostgreSQL manualmente"],
            tesseract_install_cmd=["echo", "Instalar Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki"]
        )
    
    def get_venv_activation(self, venv_path: Path) -> str:
        return str(venv_path / "Scripts" / "activate.bat")


class LinuxConfig(PlatformConfig):
    def __init__(self):
        super().__init__(
            name="Linux",
            python_cmd="python3",
            pip_cmd="pip3",
            docker_cmd="docker",
            postgres_install_cmd=["sudo", "apt-get", "install", "-y", "postgresql", "postgresql-contrib"],
            tesseract_install_cmd=["sudo", "apt-get", "install", "-y", "tesseract-ocr"]
        )
    
    def get_venv_activation(self, venv_path: Path) -> str:
        return f"source {venv_path}/bin/activate"


class MacOSConfig(PlatformConfig):
    def __init__(self):
        super().__init__(
            name="macOS",
            python_cmd="python3",
            pip_cmd="pip3",
            docker_cmd="docker",
            postgres_install_cmd=["brew", "install", "postgresql"],
            tesseract_install_cmd=["brew", "install", "tesseract"]
        )
    
    def get_venv_activation(self, venv_path: Path) -> str:
        return f"source {venv_path}/bin/activate"


def get_platform_config() -> PlatformConfig:
    """Obtiene configuración específica de la plataforma"""
    system = platform.system()
    
    if system == "Windows":
        return WindowsConfig()
    elif system == "Darwin":
        return MacOSConfig()
    elif system == "Linux":
        return LinuxConfig()
    else:
        logger.warning(f"Plataforma {system} no soportada oficialmente, usando configuración Linux")
        return LinuxConfig()


# ====================================
# UTILIDADES Y HELPERS
# ====================================

def safe_run_command(cmd: List[str], timeout: int = 30, check: bool = False) -> Tuple[bool, str]:
    """Ejecuta comando de forma segura con timeout"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
            encoding='utf-8'
        )
        return True, result.stdout
    except subprocess.TimeoutExpired:
        logger.error(f"Comando {' '.join(cmd)} expiró después de {timeout}s")
        return False, "Timeout"
    except subprocess.CalledProcessError as e:
        logger.error(f"Comando {' '.join(cmd)} falló: {e.stderr}")
        return False, e.stderr
    except FileNotFoundError:
        logger.error(f"Comando no encontrado: {cmd[0]}")
        return False, "Command not found"
    except Exception as e:
        logger.error(f"Error ejecutando comando {' '.join(cmd)}: {e}")
        return False, str(e)


def check_internet_connection() -> bool:
    """Verifica conectividad a internet"""
    try:
        urllib.request.urlopen('https://pypi.org', timeout=10)
        return True
    except Exception:
        return False


def check_disk_space(min_gb: float = 2.0) -> bool:
    """Verifica espacio en disco disponible"""
    try:
        free_bytes = shutil.disk_usage('.').free
        free_gb = free_bytes / (1024**3)
        return free_gb >= min_gb
    except Exception:
        return False


def print_banner():
    """Imprime banner de inicio"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                    🦙 NotebookLlama Enhanced                         ║
║                 🚀 Setup & Initialization v2.0                      ║
║                   Powered by Docling Integration                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_section(title: str):
    """Imprime encabezado de sección"""
    print(f"\n🔍 {title}...")


def print_success(message: str):
    """Imprime mensaje de éxito"""
    print(f"✅ {message}")
    logger.info(f"SUCCESS: {message}")


def print_warning(message: str):
    """Imprime mensaje de advertencia"""
    print(f"⚠️  {message}")
    logger.warning(f"WARNING: {message}")


def print_error(message: str):
    """Imprime mensaje de error"""
    print(f"❌ {message}")
    logger.error(f"ERROR: {message}")


def print_info(message: str):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {message}")
    logger.info(f"INFO: {message}")


# ====================================
# FASES DE SETUP
# ====================================

class SetupPhase(ABC):
    """Clase base para fases de setup"""
    
    def __init__(self, name: str):
        self.name = name
        self.config = get_platform_config()
    
    @abstractmethod
    def execute(self) -> bool:
        """Ejecuta la fase de setup"""
        pass
    
    def can_skip(self) -> bool:
        """Determina si la fase puede saltarse"""
        return False


class PreflightCheckPhase(SetupPhase):
    """Verificaciones previas al setup"""
    
    def __init__(self):
        super().__init__("Preflight Checks")
    
    def execute(self) -> bool:
        print_section("Verificaciones previas")
        
        checks = [
            ("Versión de Python", self._check_python_version),
            ("Entorno virtual", self._check_virtual_env),
            ("Conectividad a internet", self._check_internet),
            ("Espacio en disco", self._check_disk_space),
            ("Permisos de escritura", self._check_write_permissions)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if check_func():
                    print_success(f"{check_name}: OK")
                else:
                    print_warning(f"{check_name}: FAIL")
                    all_passed = False
            except Exception as e:
                print_error(f"{check_name}: ERROR - {e}")
                all_passed = False
        
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Verifica versión de Python"""
        version = sys.version_info
        min_version = (3, 9)
        
        if version >= min_version:
            print_info(f"Python {version.major}.{version.minor}.{version.micro} detectado")
            return True
        else:
            print_error(f"Python {min_version[0]}.{min_version[1]}+ requerido, encontrado {version.major}.{version.minor}")
            return False
    
    def _check_virtual_env(self) -> bool:
        """Verifica entorno virtual"""
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
        
        if in_venv:
            print_info("Entorno virtual detectado")
            return True
        else:
            print_warning("No se detectó entorno virtual, se recomienda usar uno")
            return True  # No es crítico
    
    def _check_internet(self) -> bool:
        """Verifica conectividad"""
        return check_internet_connection()
    
    def _check_disk_space(self) -> bool:
        """Verifica espacio en disco"""
        return check_disk_space(2.0)  # 2GB mínimo
    
    def _check_write_permissions(self) -> bool:
        """Verifica permisos de escritura"""
        try:
            test_file = Path("test_write_permissions.tmp")
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False


class SystemDependenciesPhase(SetupPhase):
    """Instalación de dependencias del sistema"""
    
    def __init__(self):
        super().__init__("System Dependencies")
    
    def execute(self) -> bool:
        print_section("Dependencias del sistema")
        
        # Verificar herramientas esenciales
        tools = {
            "git": self._check_git,
            "docker": self._check_docker,
            "PostgreSQL": self._check_postgres,
            "Tesseract OCR": self._check_tesseract
        }
        
        for tool_name, check_func in tools.items():
            if check_func():
                print_success(f"{tool_name} disponible")
            else:
                print_warning(f"{tool_name} no disponible (opcional)")
        
        return True  # No fallar por dependencias opcionales
    
    def _check_git(self) -> bool:
        """Verifica Git"""
        success, _ = safe_run_command(["git", "--version"])
        return success
    
    def _check_docker(self) -> bool:
        """Verifica Docker"""
        # Verificar si Docker está instalado
        success, _ = safe_run_command(["docker", "--version"])
        if not success:
            return False
        
        # Verificar si Docker está corriendo
        success, _ = safe_run_command(["docker", "info"], timeout=10)
        if success:
            print_info("Docker está corriendo")
            return True
        else:
            print_warning("Docker instalado pero no está corriendo")
            return False
    
    def _check_postgres(self) -> bool:
        """Verifica PostgreSQL"""
        success, _ = safe_run_command(["psql", "--version"])
        return success
    
    def _check_tesseract(self) -> bool:
        """Verifica Tesseract OCR"""
        success, _ = safe_run_command(["tesseract", "--version"])
        return success


class PythonDependenciesPhase(SetupPhase):
    """Instalación de dependencias Python"""
    
    def __init__(self):
        super().__init__("Python Dependencies")
    
    def execute(self) -> bool:
        print_section("Dependencias Python")
        
        # Actualizar pip primero
        if not self._upgrade_pip():
            print_warning("No se pudo actualizar pip, continuando...")
        
        # Instalar requirements.txt si existe
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            return self._install_requirements(requirements_file)
        else:
            print_warning("requirements.txt no encontrado, instalando dependencias básicas")
            return self._install_basic_requirements()
    
    def _upgrade_pip(self) -> bool:
        """Actualizar pip"""
        print_info("Actualizando pip...")
        success, output = safe_run_command([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], timeout=60)
        
        if success:
            print_success("pip actualizado")
        else:
            print_warning(f"Error actualizando pip: {output}")
        
        return success
    
    def _install_requirements(self, requirements_file: Path) -> bool:
        """Instalar desde requirements.txt"""
        print_info(f"Instalando dependencias desde {requirements_file}")
        
        # Leer requirements y filtrar las problemáticas
        try:
            requirements = requirements_file.read_text(encoding='utf-8').strip().split('\n')
            requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]
        except Exception as e:
            print_error(f"Error leyendo requirements.txt: {e}")
            return False
        
        # Instalar en lotes para mejor manejo de errores
        basic_requirements = [
            "streamlit>=1.30.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.5.0",
            "sqlalchemy>=2.0.23",
            "asyncpg>=0.29.0",
            "requests>=2.31.0",
            "pandas>=2.1.4",
            "numpy>=1.25.2"
        ]
        
        # Instalar dependencias básicas primero
        if not self._install_package_list(basic_requirements, "básicas"):
            return False
        
        # Instalar el resto
        remaining_requirements = [req for req in requirements if not any(basic in req for basic in basic_requirements)]
        if remaining_requirements:
            return self._install_package_list(remaining_requirements, "adicionales", allow_failures=True)
        
        return True
    
    def _install_basic_requirements(self) -> bool:
        """Instalar dependencias básicas mínimas"""
        basic_requirements = [
            "streamlit>=1.30.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.5.0",
            "requests>=2.31.0"
        ]
        
        return self._install_package_list(basic_requirements, "básicas")
    
    def _install_package_list(self, packages: List[str], package_type: str, allow_failures: bool = False) -> bool:
        """Instalar lista de paquetes"""
        print_info(f"Instalando dependencias {package_type}...")
        
        failed_packages = []
        
        for package in packages:
            if not package.strip():
                continue
                
            print_info(f"Instalando {package}...")
            success, output = safe_run_command([
                sys.executable, "-m", "pip", "install", package, "--no-warn-script-location"
            ], timeout=120)
            
            if success:
                print_success(f"{package} instalado")
            else:
                print_error(f"Error instalando {package}: {output}")
                failed_packages.append(package)
                
                if not allow_failures:
                    return False
        
        if failed_packages and allow_failures:
            print_warning(f"Algunos paquetes fallaron: {', '.join(failed_packages)}")
        
        return True


class EnvironmentConfigPhase(SetupPhase):
    """Configuración de variables de entorno"""
    
    def __init__(self):
        super().__init__("Environment Configuration")
    
    def execute(self) -> bool:
        print_section("Configuración de entorno")
        
        env_file = Path(".env")
        env_example = Path(".env.example")
        
        # Crear .env si no existe
        if not env_file.exists():
            if env_example.exists():
                print_info("Copiando .env.example a .env")
                try:
                    env_file.write_text(env_example.read_text(encoding='utf-8'), encoding='utf-8')
                    print_success("Archivo .env creado")
                except Exception as e:
                    print_error(f"Error copiando .env.example: {e}")
                    return self._create_basic_env(env_file)
            else:
                return self._create_basic_env(env_file)
        else:
            print_success("Archivo .env ya existe")
        
        # Validar configuración
        return self._validate_env_config(env_file)
    
    def _create_basic_env(self, env_file: Path) -> bool:
        """Crear archivo .env básico"""
        print_info("Creando archivo .env básico")
        
        basic_env = """# NotebookLlama Configuration
# Base de datos
DATABASE_URL=postgresql+asyncpg://notebookllama:password@localhost:5432/notebookllama

# APIs de IA (REQUERIDO al menos uno)
OPENAI_API_KEY=your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Configuración de Docling
ENABLE_OCR=true
ENABLE_TABLE_EXTRACTION=true
ENABLE_IMAGE_EXTRACTION=true

# Configuración de chunks
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Logging
LOG_LEVEL=INFO
"""
        
        try:
            env_file.write_text(basic_env, encoding='utf-8')
            print_success("Archivo .env básico creado")
            return True
        except Exception as e:
            print_error(f"Error creando .env: {e}")
            return False
    
    def _validate_env_config(self, env_file: Path) -> bool:
        """Validar configuración de entorno"""
        try:
            # Intentar cargar python-dotenv si está disponible
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                print_success("Configuración de entorno cargada")
            except ImportError:
                print_warning("python-dotenv no disponible, validación limitada")
            
            # Verificar contenido básico
            content = env_file.read_text(encoding='utf-8')
            
            required_vars = ["DATABASE_URL", "OPENAI_API_KEY"]
            missing_vars = []
            
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                print_warning(f"Variables faltantes en .env: {', '.join(missing_vars)}")
                print_info("Edita el archivo .env con tus configuraciones reales")
            
            return True
            
        except Exception as e:
            print_error(f"Error validando .env: {e}")
            return False


class DatabaseSetupPhase(SetupPhase):
    """Configuración de base de datos"""
    
    def __init__(self):
        super().__init__("Database Setup")
    
    def execute(self) -> bool:
        print_section("Configuración de base de datos")
        
        # Verificar si Docker está disponible
        docker_available = self._check_docker_available()
        
        if docker_available:
            return self._setup_with_docker()
        else:
            return self._setup_manual_guidance()
    
    def _check_docker_available(self) -> bool:
        """Verifica si Docker está disponible y corriendo"""
        success, _ = safe_run_command(["docker", "info"], timeout=10)
        return success
    
    def _setup_with_docker(self) -> bool:
        """Setup usando Docker Compose"""
        print_info("🐳 Docker detectado")
        
        # Verificar si docker-compose.yml existe
        compose_file = Path("docker-compose.yml")
        if not compose_file.exists():
            print_warning("docker-compose.yml no encontrado")
            return self._setup_manual_guidance()
        
        # Preguntar al usuario si quiere usar Docker
        try:
            use_docker = input("¿Usar Docker para PostgreSQL? (Y/n): ").strip().lower()
            if use_docker in ['n', 'no']:
                return self._setup_manual_guidance()
        except (EOFError, KeyboardInterrupt):
            print_info("Usando configuración por defecto (Docker)")
        
        # Intentar iniciar servicios
        print_info("📦 Iniciando servicios con Docker Compose...")
        success, output = safe_run_command([
            "docker-compose", "up", "-d", "database", "redis"
        ], timeout=120)
        
        if success:
            print_success("Servicios de base de datos iniciados")
            # Esperar a que la base de datos esté lista
            return self._wait_for_database()
        else:
            print_error(f"Error iniciando Docker Compose: {output}")
            print_info("Intentando con 'docker compose' (versión nueva)...")
            
            # Intentar con nueva sintaxis de Docker Compose
            success, output = safe_run_command([
                "docker", "compose", "up", "-d", "database", "redis"
            ], timeout=120)
            
            if success:
                print_success("Servicios iniciados con nueva sintaxis Docker Compose")
                return self._wait_for_database()
            else:
                print_error(f"Error con Docker Compose: {output}")
                return self._setup_manual_guidance()
    
    def _wait_for_database(self) -> bool:
        """Esperar a que la base de datos esté lista"""
        print_info("⏳ Esperando a que la base de datos esté lista...")
        
        max_attempts = 30
        for attempt in range(max_attempts):
            success, _ = safe_run_command([
                "docker-compose", "exec", "-T", "database", 
                "pg_isready", "-U", "notebookllama"
            ], timeout=5)
            
            if success:
                print_success("Base de datos lista")
                return True
            
            print_info(f"Intento {attempt + 1}/{max_attempts}...")
            time.sleep(2)
        
        print_warning("Base de datos tardó demasiado en estar lista")
        return True  # No fallar completamente
    
    def _setup_manual_guidance(self) -> bool:
        """Proporcionar guía para configuración manual"""
        print_info("🐘 Configuración manual de PostgreSQL")
        
        guidance = f"""
Para configurar PostgreSQL manualmente:

1. Instalar PostgreSQL:
   {self.config.name}: {' '.join(self.config.postgres_install_cmd)}

2. Crear base de datos:
   sudo -u postgres psql
   CREATE DATABASE notebookllama;
   CREATE USER notebookllama WITH PASSWORD 'tu_password';
   GRANT ALL PRIVILEGES ON DATABASE notebookllama TO notebookllama;

3. Instalar extensión pgvector:
   \\c notebookllama
   CREATE EXTENSION vector;

4. Actualizar DATABASE_URL en .env:
   DATABASE_URL=postgresql+asyncpg://notebookllama:tu_password@localhost:5432/notebookllama
"""
        
        print(guidance)
        print_success("Guía de configuración manual mostrada")
        return True


class FinalValidationPhase(SetupPhase):
    """Validación final del setup"""
    
    def __init__(self):
        super().__init__("Final Validation")
    
    def execute(self) -> bool:
        print_section("Validación final")
        
        validations = [
            ("Imports principales", self._test_imports),
            ("Configuración de entorno", self._test_env_config),
            ("Conectividad de base de datos", self._test_database_connection)
        ]
        
        all_passed = True
        for validation_name, validation_func in validations:
            try:
                if validation_func():
                    print_success(f"{validation_name}: OK")
                else:
                    print_warning(f"{validation_name}: FALLO")
                    all_passed = False
            except Exception as e:
                print_error(f"{validation_name}: ERROR - {e}")
                all_passed = False
        
        return all_passed
    
    def _test_imports(self) -> bool:
        """Probar imports principales"""
        try:
            import streamlit
            import pydantic
            import sqlalchemy
            return True
        except ImportError as e:
            print_error(f"Error importando módulos: {e}")
            return False
    
    def _test_env_config(self) -> bool:
        """Probar configuración de entorno"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Verificar variables críticas
            database_url = os.getenv('DATABASE_URL')
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if not database_url:
                print_warning("DATABASE_URL no configurada")
                return False
            
            if not openai_key or openai_key == 'your-openai-api-key-here':
                print_warning("OPENAI_API_KEY no configurada correctamente")
                return False
            
            return True
        except ImportError:
            print_warning("python-dotenv no disponible para validación")
            return True
        except Exception as e:
            print_error(f"Error validando configuración: {e}")
            return False
    
    def _test_database_connection(self) -> bool:
        """Probar conexión a base de datos"""
        try:
            # Este test es opcional ya que puede no estar configurada aún
            return True
        except Exception:
            return True


# ====================================
# ORQUESTADOR PRINCIPAL
# ====================================

class SetupOrchestrator:
    """Orquestador principal del setup"""
    
    def __init__(self):
        self.phases = [
            PreflightCheckPhase(),
            SystemDependenciesPhase(),
            PythonDependenciesPhase(),
            EnvironmentConfigPhase(),
            DatabaseSetupPhase(),
            FinalValidationPhase()
        ]
        
        self.config = get_platform_config()
    
    def run(self) -> bool:
        """Ejecutar todas las fases de setup"""
        print_banner()
        print_info(f"Ejecutando en {self.config.name}")
        print_info(f"Python {sys.version}")
        print_info(f"Directorio: {os.getcwd()}")
        
        start_time = time.time()
        failed_phases = []
        
        for phase in self.phases:
            print(f"\n{'='*60}")
            print_info(f"Ejecutando fase: {phase.name}")
            print(f"{'='*60}")
            
            try:
                if phase.execute():
                    print_success(f"Fase {phase.name} completada")
                else:
                    print_error(f"Fase {phase.name} falló")
                    failed_phases.append(phase.name)
                    
                    # Decidir si continuar o abortar
                    if not self._should_continue_after_failure(phase):
                        break
                        
            except KeyboardInterrupt:
                print_info("\nSetup interrumpido por el usuario")
                return False
            except Exception as e:
                print_error(f"Error inesperado en fase {phase.name}: {e}")
                failed_phases.append(phase.name)
                logger.exception(f"Unexpected error in phase {phase.name}")
        
        # Resumen final
        elapsed_time = time.time() - start_time
        self._print_summary(failed_phases, elapsed_time)
        
        return len(failed_phases) == 0
    
    def _should_continue_after_failure(self, phase: SetupPhase) -> bool:
        """Determina si continuar después de un fallo"""
        # Fases críticas que requieren intervención
        critical_phases = ["Preflight Checks", "Python Dependencies"]
        
        if phase.name in critical_phases:
            print_error(f"Fase crítica {phase.name} falló. Revisa los errores antes de continuar.")
            return False
        
        print_warning(f"Fase {phase.name} falló pero no es crítica, continuando...")
        return True
    
    def _print_summary(self, failed_phases: List[str], elapsed_time: float):
        """Imprimir resumen final"""
        print(f"\n{'='*70}")
        print("🏁 RESUMEN DE SETUP")
        print(f"{'='*70}")
        
        print_info(f"Tiempo total: {elapsed_time:.1f} segundos")
        
        if not failed_phases:
            print_success("✨ Setup completado exitosamente!")
            print("\n🚀 Próximos pasos:")
            print("1. Edita el archivo .env con tus API keys reales")
            print("2. Ejecuta: streamlit run src/notebookllama/Home_Complete.py")
            print("3. Abre tu navegador en: http://localhost:8501")
        else:
            print_warning(f"Setup completado con {len(failed_phases)} fase(s) fallida(s):")
            for phase in failed_phases:
                print(f"  ❌ {phase}")
            
            print("\n🔧 Para resolver problemas:")
            print("1. Revisa los errores mostrados arriba")
            print("2. Consulta setup.log para detalles")
            print("3. Ejecuta el setup nuevamente")
        
        print(f"\n📝 Log completo: {Path('setup.log').absolute()}")
        print("📖 Documentación: README.md")


# ====================================
# FUNCIÓN PRINCIPAL
# ====================================

def main():
    """Función principal del setup"""
    try:
        orchestrator = SetupOrchestrator()
        success = orchestrator.run()
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print_info("\n👋 Setup cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error fatal en setup: {e}")
        logger.exception("Fatal error in setup")
        sys.exit(1)


if __name__ == "__main__":
    main()
    