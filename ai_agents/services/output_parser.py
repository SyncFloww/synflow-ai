import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OutputParser:
    def sanitize_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
        elif text.startswith("```markdown"):
            text = text[11:]
            if text.endswith("```"):
                text = text[:-3]
        elif text.startswith("```"):
            text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()

    def parse_json(self, raw_text: str, fallback_data: Optional[Dict] = None) -> Dict[str, Any]:
        clean_text = self.sanitize_text(raw_text)
        try:
            return json.loads(clean_text)
        except Exception as e:
            logger.warning(f"OutputParser failed to parse JSON output: {e}")
            return fallback_data or {}
