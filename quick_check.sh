#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${YELLOW}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Check for sudo privileges
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run with sudo"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
apt update
apt upgrade -y

# Install Python 3.10 if not present
print_status "Installing Python and dependencies..."
apt install -y python3-pip python3.10-venv python3-dev build-essential libssl-dev libffi-dev python3-setuptools

# Install Redis
print_status "Installing and configuring Redis..."
apt install -y redis-server
systemctl enable redis-server
systemctl start redis-server

# Test Redis connection
print_status "Testing Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
    systemctl status redis-server
    exit 1
fi

# Get the actual user who ran sudo
ACTUAL_USER=$(who am i | awk '{print $1}')
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)
PROJECT_DIR="$ACTUAL_HOME/lang_stack_proj"

# Create project directory
print_status "Creating project directory..."
mkdir -p $PROJECT_DIR
chown $ACTUAL_USER:$ACTUAL_USER $PROJECT_DIR
cd $PROJECT_DIR

# Create necessary directories with proper permissions
print_status "Creating required directories..."
mkdir -p uploads vector_store
chown -R $ACTUAL_USER:$ACTUAL_USER uploads vector_store

# Create virtual environment
print_status "Setting up Python virtual environment..."
sudo -u $ACTUAL_USER python3 -m venv venv
source venv/bin/activate

# Install Python packages
print_status "Installing Python packages..."
sudo -u $ACTUAL_USER venv/bin/pip install --upgrade pip
sudo -u $ACTUAL_USER venv/bin/pip install fastapi uvicorn python-dotenv langchain langchain-community langgraph langsmith redis openai pydantic pydantic-settings faiss-cpu pypdf tiktoken prometheus_client

# Create or update .env file
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    cat << EOF > .env
OPENAI_API_KEY=your_key_here
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=your_project_name
REDIS_HOST=localhost
REDIS_PORT=6379
MODEL_NAME=gpt-3.5-turbo
TEMPERATURE=0.7
EOF
    chown $ACTUAL_USER:$ACTUAL_USER .env
    print_success ".env file created - Please edit with your API keys"
fi

print_success "Setup complete!"
print_status "Next steps:"
echo "1. Add your OpenAI API key to .env file:"
echo "   nano $PROJECT_DIR/.env"
echo "2. Start the server with:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python src/main.py"