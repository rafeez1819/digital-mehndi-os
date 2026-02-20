#!/bin/bash
# 🌸 Digital Mehndi OS — Setup Script

set -e
echo "🌸 Setting up Digital Mehndi OS..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  Created .env — add your ANTHROPIC_API_KEY!"
fi

# Create DB directory
mkdir -p backend/db

# Run migrations
cd backend
python manage.py makemigrations emotional_kernel memory api
python manage.py migrate

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env → add your ANTHROPIC_API_KEY"
echo "  2. source venv/bin/activate"
echo "  3. cd backend && python manage.py runserver"
echo "  4. Open http://localhost:8000"
echo ""
echo "🌸 The pattern awaits."
