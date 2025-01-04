#!/bin/bash

# Check Python version
if python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
    echo "Python version OK"
else
    echo "Error: Python 3.10 or higher is required"
    exit 1
fi

# Install Redis
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    brew install redis
    brew services start redis
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # Linux
    sudo apt update
    sudo apt install redis-server -y
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
else
    echo "Unsupported operating system"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat << EOF > .env
OPENAI_API_KEY=your_key_here
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=your_project_name
REDIS_HOST=localhost
REDIS_PORT=6379
MODEL_NAME=gpt-3.5-turbo
TEMPERATURE=0.7
EOF
    echo "Created .env file - please edit with your API keys"
fi

echo "Setup complete!"