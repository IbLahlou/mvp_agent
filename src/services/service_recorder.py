from datetime import datetime
import uuid
import os
from typing import Dict, Optional

class ServiceRecorder:
    def __init__(self, records_dir: str = "service_records"):
        self.records_dir = records_dir
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)

    async def generate_record_content(self, interaction_data: Dict) -> str:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        record_id = f"record_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Generate plain text log content
        return f"""Service Record - {record_id}
Timestamp: {timestamp}
Endpoint: {interaction_data.get('endpoint', 'Unknown')}
Type: {interaction_data.get('type', 'General')}
Status: {interaction_data.get('status', 'Completed')}

Interaction Details:
{interaction_data.get('details', 'No details provided')}

Response:
{interaction_data.get('response', 'No response recorded')}
"""

    async def save_record(self, content: str) -> str:
        record_id = f"record_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        file_path = os.path.join(self.records_dir, f"{record_id}.log")  # Save as .log file
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return record_id

    async def process_interaction(self, interaction_data: Dict) -> Optional[str]:
        try:
            # Only log interactions with the /agent endpoint
            if interaction_data.get("endpoint") != "/agent":
                return None  # Skip logging for all other endpoints

            # Process and save interactions with /agent
            content = await self.generate_record_content(interaction_data)
            return await self.save_record(content)
        except Exception as e:
            print(f"Record processing error: {str(e)}")
            return None
