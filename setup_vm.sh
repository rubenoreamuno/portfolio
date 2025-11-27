#!/bin/bash
# Setup script for GCE VM - installs dependencies and prepares environment

set -e

echo "Setting up VM environment for portfolio testing..."

# Update system
echo "Updating system packages..."
sudo apt-get update -qq

# Install Python and pip
echo "Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install Docker (if not present)
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Git (if not present)
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    sudo apt-get install -y git
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel

echo ""
echo "✓ VM setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone or copy the portfolio repository"
echo "2. Run: chmod +x test_all_projects.sh"
echo "3. Run: ./test_all_projects.sh"

