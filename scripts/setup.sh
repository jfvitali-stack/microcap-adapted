#!/bin/bash
# Development setup script for micro-cap portfolio tracker

echo "🚀 Setting up Micro-Cap Portfolio Tracker"
echo "========================================"

# Create virtual environment
echo "📦 Creating virtual environment..."
python -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create required directories
echo "📁 Creating directory structure..."
mkdir -p data docs reports state excel_reports backups

# Copy environment template
if [ ! -f .env ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "Please edit .env file with your API key"
fi

# Initialize portfolio state
if [ ! -f state/portfolio_state.json ]; then
    echo "💰 Initializing portfolio state..."
    cat > state/portfolio_state.json << EOF
{
  "cash": 0,
  "holdings": {
    "GEVO": 299,
    "FEIM": 10,
    "ARQ": 37,
    "UPXI": 17
  },
  "last_valuation_date": "2025-08-08"
}
EOF
fi

# Test API connection (if API key provided)
echo "🔍 Testing setup..."
python monitor.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Alpha Vantage API key"
echo "2. Run: python main.py"
echo "3. Check docs/index.html for dashboard"
echo ""
echo "For GitHub deployment:"
echo "1. Add ALPHAVANTAGE_API_KEY to GitHub Secrets"
echo "2. Enable GitHub Pages in repository settings"
echo "3. Workflows will run automatically"
