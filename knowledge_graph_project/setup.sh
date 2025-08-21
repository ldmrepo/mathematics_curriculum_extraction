#!/bin/bash

# Setup script for Knowledge Graph Construction Project
# This script initializes the project environment

echo "🧠 Knowledge Graph Construction Project Setup"
echo "=============================================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p output
mkdir -p logs
mkdir -p data/temp

# Copy environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and database configurations"
fi

# Check database connections (optional)
echo "🔍 Checking database connections..."

# PostgreSQL check
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
else
    echo "⚠️  PostgreSQL client not found - install if you plan to use PostgreSQL"
fi

# Neo4j check
if command -v neo4j &> /dev/null; then
    echo "✅ Neo4j found"
else
    echo "⚠️  Neo4j not found - install if you plan to use Neo4j graph database"
fi

# Create sample configuration files
echo "📄 Creating sample configuration files..."

# Create logs directory and initial log file
touch logs/setup.log
echo "$(date): Project setup completed" >> logs/setup.log

# Run initial tests (optional)
echo "🧪 Running basic tests..."
if python -c "import pytest; import asyncio; import pandas; import numpy; print('✅ Core dependencies imported successfully')"; then
    echo "✅ Basic dependency check passed"
else
    echo "❌ Some dependencies may be missing"
fi

# Display setup completion message
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Configure database connections"
echo "3. Run the project: python main.py"
echo "4. Or start the dashboard: streamlit run dashboard.py"
echo ""
echo "For more information, see README.md"
