#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[*] Setting up logging system...${NC}"

# Create necessary directories
mkdir -p src/services
mkdir -p src/middleware
mkdir -p logs

# Create the logger service
echo -e "${YELLOW}[*] Creating logger service...${NC}"
cat > src/services/request_logger.py << 'EOL'
from datetime import datetime
import os
import json
from typing import Dict, Any

class RequestLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    async def log_interaction(self, data: Dict[str, Any]):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.log_dir}/log_{timestamp}.md"

        markdown = f"""# Service Log {timestamp}

## Request
- Endpoint: {data.get('endpoint', 'N/A')}
- Method: {data.get('method', 'N/A')}
- Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

## Details
```json
{json.dumps(data.get('request_data', {}), indent=2)}
```

## Response
```json
{json.dumps(data.get('response', {}), indent=2)}
```

## Additional Info
- Duration: {data.get('duration', 'N/A')}ms
- Status: {data.get('status', 'N/A')}
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown)
EOL

# Create middleware
echo -e "${YELLOW}[*] Creating middleware...${NC}"
cat > src/middleware/logging_middleware.py << 'EOL'
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.request_logger import RequestLogger
import time
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = RequestLogger()

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture request data
        request_data = {
            'endpoint': str(request.url),
            'method': request.method,
            'query_params': dict(request.query_params),
            'path_params': request.path_params,
        }

        # Try to get request body if present
        try:
            body = await request.body()
            if body:
                request_data['body'] = json.loads(body)
        except:
            pass

        # Process request and capture response
        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)

        # Log the interaction
        await self.logger.log_interaction({
            'endpoint': str(request.url),
            'method': request.method,
            'request_data': request_data,
            'response': {
                'status_code': response.status_code,
                'headers': dict(response.headers)
            },
            'duration': duration,
            'status': 'success' if response.status_code < 400 else 'error'
        })

        return response
EOL

# Create view logs script
echo -e "${YELLOW}[*] Creating log viewer...${NC}"
cat > view_logs.sh << 'EOL'
#!/bin/bash

LOGS_DIR="logs"

case "$1" in
    --latest)
        latest=$(ls -t "$LOGS_DIR"/*.md 2>/dev/null | head -n 1)
        if [ -f "$latest" ]; then
            cat "$latest"
        else
            echo "No logs found"
        fi
        ;;
    --list)
        ls -lt "$LOGS_DIR"/*.md 2>/dev/null
        ;;
    --clear)
        rm -f "$LOGS_DIR"/*.md
        echo "Logs cleared"
        ;;
    *)
        echo "Usage: $0 [--latest|--list|--clear]"
        ;;
esac
EOL

chmod +x view_logs.sh

echo -e "${GREEN}[+] Setup complete!${NC}"
echo -e "${YELLOW}[*] To enable logging, add these lines to your main.py:${NC}"
echo '
from src.middleware.logging_middleware import LoggingMiddleware
app.add_middleware(LoggingMiddleware)
'

echo -e "${YELLOW}[*] Directory structure created:${NC}"
tree src/

echo -e "${YELLOW}[*] To view logs:${NC}"
echo "./view_logs.sh --latest  # View latest log"
echo "./view_logs.sh --list    # List all logs"
echo "./view_logs.sh --clear   # Clear all logs"