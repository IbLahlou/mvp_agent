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
