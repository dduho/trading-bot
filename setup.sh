#!/bin/bash

echo "========================================="
echo "Trading Bot Setup"
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your API credentials"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your exchange API credentials"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the bot: python run_bot.py"
echo ""
echo "For backtesting: python backtest.py"
echo ""
