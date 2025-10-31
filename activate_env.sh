#!/bin/bash
# Activation script for the virtual environment
# Usage: source activate_env.sh

echo "Activating virtual environment..."
source venv/bin/activate
echo "Virtual environment activated! You can now run:"
echo "  python training/scripts/train.py"
echo ""
echo "To deactivate, run: deactivate"
