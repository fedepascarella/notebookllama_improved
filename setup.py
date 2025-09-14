#!/usr/bin/env python3
"""
Script de inicialización para NotebookLlama Enhanced
Configura el entorno y verifica dependencias
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_banner():
    """Mostrar banner de bienvenida"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                    📚 NotebookLlama Enhanced                         ║
║                    🚀 Setup & Initialization                         ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Error: Se requiere Python 3.10 o superior")
        print(f"   Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True


def check_dependencies():
    """Verificar dependencias del sistema"""
    dependencies = {
        'docker': 'Docker (opcional, para PostgreSQL)',
        'git': 'Git',
        'pip': 'Python package manager'
    }
    
    missing = []
    for cmd, desc in dependencies.items():
        try:
            subprocess.run([cmd, '--version'], 
                         capture_output=True, check=True)
            print(f"✅ {desc} disponible")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠️  {desc} no encontrado")
            if cmd != 'docker':  # Docker es opcional
                missing.append(cmd)
    
    return len(missing) == 0


def setup_environment():
    """Configurar archivo de entorno"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creando archivo .env desde .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Archivo .env creado")
            print("⚠️  IMPORTANTE: Edita .env con tus credenciales de API")
        else:
            print("❌ No se encontró .env.example")
            return False
    else:
        print("✅ Archivo .env ya existe")
    
    return True


def install_python_dependencies():
    """Instalar dependencias de Python"""
    print("📦 Instalando dependencias de Python...")
    
    try:
        # Verificar si estamos en un entorno virtual
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ Entorno virtual detectado")
        else:
            print("⚠️  No se detectó entorno virtual")
            response = input("¿Continuar sin entorno virtual? (y/N): ")
            if response.lower() != 'y':
                print("💡 Crea un entorno virtual con: python -m venv venv")
                return False
        
        # Instalar dependencias
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], check=True)
        
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-e', '.'
        ], check=True)
        
        print("✅ Dependencias instaladas correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False


def setup_database():
    """Configurar base de datos"""
    print("\n🐘 Configuración de PostgreSQL")
    
    # Verificar si Docker está disponible
    try:
        subprocess.run(['docker', '--version'], 
                      capture_output=True, check=True)
        docker_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        docker_available = False
    
    if docker_available:
        print("🐳 Docker detectado")
        response = input("¿Usar Docker para PostgreSQL? (Y/n): ")
        if response.lower() != 'n':
            try:
                print("📦 Iniciando servicios con Docker Compose...")
                subprocess.run(['docker-compose', 'up', '-d'], check=True)
                print("✅ PostgreSQL iniciado con Docker")
                return True
            except subprocess.CalledProcessError:
                print("❌ Error iniciando Docker Compose")
                return False
    
    print("📋 Para configuración manual de PostgreSQL:")
    print("   1. Instala PostgreSQL 15+")
    print("   2. Instala la extensión pgvector")
    print("   3. Crea la base de datos 'notebookllama_enhanced'")
    print("   4. Configura las credenciales en .env")
    
    return True


def verify_apis():
    """Verificar configuración de APIs"""
    print("\n🔑 Verificando configuración de APIs")
    
    # Cargar variables de entorno
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    apis = {
        'OPENAI_API_KEY': 'OpenAI (requerido)',
        'ELEVENLABS_API_KEY': 'ElevenLabs (opcional, para podcasts)'
    }
    
    all_good = True
    for key, desc in apis.items():
        value = os.getenv(key)
        if value and value != f"sk-***":
            print(f"✅ {desc} configurado")
        else:
            status = "❌" if key == 'OPENAI_API_KEY' else "⚠️ "
            print(f"{status} {desc} no configurado")
            if key == 'OPENAI_API_KEY':
                all_good = False
    
    return all_good


def test_installation():
    """Probar la instalación"""
    print("\n🧪 Probando instalación...")
    
    try:
        # Test de importaciones básicas
        from src.notebookllama.docling_processor import DOCLING_PROCESSOR
        print("✅ Docling processor cargado")
        
        from src.notebookllama.postgres_manager import DOCUMENT_MANAGER
        print("✅ PostgreSQL manager cargado")
        
        from src.notebookllama.enhanced_workflow import WF
        print("✅ Enhanced workflow cargado")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Warning durante la carga: {e}")
        return True  # No crítico


def main():
    """Función principal"""
    print_banner()
    
    # Verificaciones
    checks = [
        ("Versión de Python", check_python_version),
        ("Dependencias del sistema", check_dependencies),
        ("Archivo de entorno", setup_environment),
        ("Dependencias Python", install_python_dependencies),
        ("Base de datos", setup_database),
        ("Configuración APIs", verify_apis),
        ("Instalación", test_installation),
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n🔍 {name}...")
        results[name] = check_func()
    
    # Resumen
    print("\n" + "="*70)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("="*70)
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    if all(results.values()):
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\n🚀 Para iniciar la aplicación:")
        print("   streamlit run src/notebookllama/Enhanced_Home.py")
    else:
        print("\n⚠️  Algunos elementos requieren atención.")
        print("   Revisa los errores anteriores antes de continuar.")
    
    print("\n📚 Documentación completa disponible en README.md")


if __name__ == "__main__":
    main()
