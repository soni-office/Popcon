#!/bin/bash
# Setup script for AI Job Seeker Agent

echo "Setting up AI Job Seeker Agent..."
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# Tavily AI API Key
TAVILY_API_KEY=your_tavily_api_key_here

# Hunter.io API Key
HUNTER_API_KEY=your_hunter_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=Your Name
EOF
    echo "✓ Created .env file"
    echo "Please edit .env and add your API keys"
else
    echo "✓ .env file already exists"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To install dependencies, run:"
echo "  pip install -r requirements.txt"
echo ""
