import json
import re
from typing import Any

import httpx

from app.config import settings


class OllamaClient:
    """
    Lightweight Ollama client for text and vision-capable models.

    Text agents use:
    - settings.OLLAMA_MODEL

    Vision agent uses:
    - settings.OLLAMA_VISION_MODEL
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.vision_model = settings.OLLAMA_VISION_MODEL

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        """
        Extract valid JSON from an LLM response.

        The model should return JSON directly, but this function also handles
        cases where the model adds extra text around the JSON.
        """

        if not raw_text:
            raise ValueError("LLM returned an empty response.")

        raw_text = raw_text.strip()

        # Direct JSON
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return parsed

            raise ValueError(f"LLM returned JSON, but it is not an object: {parsed}")

        except json.JSONDecodeError:
            pass

        # Remove markdown JSON fences if the model adds them
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return parsed

            raise ValueError(f"LLM returned JSON, but it is not an object: {parsed}")

        except json.JSONDecodeError:
            pass

        # Fallback: extract first JSON object from text
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)

        if not match:
            raise ValueError(f"LLM did not return JSON. Raw response: {raw_text}")

        parsed = json.loads(match.group(0))

        if not isinstance(parsed, dict):
            raise ValueError(f"LLM returned JSON, but it is not an object: {parsed}")

        return parsed

    def generate_text(self, prompt: str) -> str:
        """
        Generate a text response using the default text model.
        """

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_predict": 700,
            },
        }

        try:
            with httpx.Client(timeout=300) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama text model request failed with status "
                f"{exc.response.status_code}: {exc.response.text}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. Error: {exc}"
            ) from exc

        return data.get("response", "").strip()

    def generate_json(self, prompt: str) -> dict[str, Any]:
        """
        Generate JSON using the default text model.
        """

        raw_text = self.generate_text(prompt)
        return self._extract_json(raw_text)

    def generate_vision_json(
        self,
        prompt: str,
        image_base64: str,
    ) -> dict[str, Any]:
        """
        Generate JSON from an image using an Ollama vision-capable model.

        Important:
        image_base64 must be pure base64, without:
        data:image/png;base64,

        The Vision Agent should clean the image before calling this function.
        """

        if not image_base64:
            raise ValueError("image_base64 is required for vision generation.")

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.vision_model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_predict": 900,
            },
        }

        try:
            with httpx.Client(timeout=300) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama vision model request failed with status "
                f"{exc.response.status_code}: {exc.response.text}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to Ollama at {self.base_url}. Error: {exc}"
            ) from exc

        raw_text = data.get("response", "").strip()
        return self._extract_json(raw_text)


ollama_client = OllamaClient()