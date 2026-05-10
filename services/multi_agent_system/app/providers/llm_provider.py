import json
import re
from typing import Any

import httpx

from app.config import settings


class OllamaClient:
    """
    Lightweight Ollama client.
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    def generate_text(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_predict": 500,
            },
        }

        with httpx.Client(timeout=300) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return data.get("response", "").strip()

    def generate_json(self, prompt: str) -> dict[str, Any]:
        raw_text = self.generate_text(prompt)

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)

        if not match:
            raise ValueError(f"LLM did not return JSON. Raw response: {raw_text}")

        return json.loads(match.group(0))


ollama_client = OllamaClient()