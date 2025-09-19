#!/bin/bash

echo "========================================"
echo "  NotebookLlama Enhanced - Linux Startup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker version &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not running!"
    echo "Please start Docker first."
    exit 1
fi

echo -e "${GREEN}[1/5]${NC} Starting Docker services..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Failed to start Docker services"
    exit 1
fi

echo ""
echo -e "${GREEN}[2/5]${NC} Waiting for PostgreSQL to be ready..."
sleep 5

# Check PostgreSQL connection
docker exec notebookllama-enhanced-postgres-1 pg_isready -U postgres &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[WARNING]${NC} PostgreSQL might not be fully ready yet"
    echo "Waiting additional 5 seconds..."
    sleep 5
fi

echo ""
echo -e "${GREEN}[3/5]${NC} Activating Python virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}[WARNING]${NC} Virtual environment not found!"
    echo "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo -e "${GREEN}[4/5]${NC} Checking environment variables..."
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR]${NC} .env file not found!"
    echo "Please create .env file with your API keys"
    echo "Copy .env.example to .env and update the values"
    exit 1
fi

echo ""
echo -e "${GREEN}[5/5]${NC} Starting Streamlit application..."
echo ""
echo "========================================"
echo "  Services Status:"
echo "========================================"
docker-compose ps
echo ""
echo "========================================"
echo "  Application URLs:"
echo "========================================"
echo "  Main App:     http://localhost:8501"
echo "  Database UI:  http://localhost:8080"
echo "  Jaeger:       http://localhost:16686"
echo "========================================"
echo ""
echo "Starting application in 3 seconds..."
sleep 3

# Start Streamlit
streamlit run src/notebookllama/Enhanced_Home.py

echo ""
echo "Application stopped."
echo ""
read -p "Would you like to stop Docker services? (y/n): " stop_docker
if [[ $stop_docker =~ ^[Yy]$ ]]; then
    echo "Stopping Docker services..."
    docker-compose stop
    echo "Docker services stopped."
fi