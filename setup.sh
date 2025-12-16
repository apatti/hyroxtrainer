#!/bin/bash

# Hyrox Trainer Setup Script

echo "Setting up Hyrox Trainer..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.9+ first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "IMPORTANT: .env file not found!"
    echo "Please create a .env file with your credentials:"
    echo ""
    echo "1. Copy the example file:"
    echo "   cp .env.example .env"
    echo ""
    echo "2. Edit .env and add your:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo "   - ANTHROPIC_API_KEY (or OPENAI_API_KEY)"
    echo ""
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "1. source venv/bin/activate"
echo "2. streamlit run app.py"
echo ""
echo "Don't forget to run the SQL schema in your Supabase project!"
echo "The schema file is located at: src/database/schema.sql"
