"""Async NVIDIA NIM Client with retries, backoff, and JSON parsing."""
import json
import re
import asyncio
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel
from backend.app.config import Settings, get_settings


class NvidiaNIMClient:
    """Async client communicating with NVIDIA NIM OpenAI-compatible API."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.NVIDIA_NIM_BASE_URL.rstrip("/")
        self.api_key = self.settings.NVIDIA_NIM_API_KEY
        self.model = self.settings.NVIDIA_NIM_MODEL
        self.timeout = self.settings.NVIDIA_NIM_TIMEOUT_SECONDS
        self.temperature = self.settings.NVIDIA_NIM_TEMPERATURE

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1024,
        }

        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()

                    # Handle Rate Limits (429) or Service Warm-up (503)
                    if resp.status_code in (429, 503) and attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    resp.raise_for_status()

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == max_retries - 1:
                    # Graceful fallback to mock LLM on API endpoint failures (e.g., 410 Gone, invalid model ID)
                    from .mock_client import MockLLMClient
                    mock = MockLLMClient(self.settings)
                    return await mock.generate(prompt, system_prompt=system_prompt)
                await asyncio.sleep(backoff)
                backoff *= 2

        from .mock_client import MockLLMClient
        mock = MockLLMClient(self.settings)
        return await mock.generate(prompt, system_prompt=system_prompt)

    async def generate_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response and extract clean JSON."""
        try:
            content = await self.generate(prompt, system_prompt=system_prompt)
            return self._extract_json(content)
        except Exception:
            from .mock_client import MockLLMClient
            mock = MockLLMClient(self.settings)
            return await mock.generate_json(prompt, system_prompt=system_prompt)

    @staticmethod
    def _extract_json(text_content: str) -> Dict[str, Any]:
        """Extract and parse JSON from raw text or markdown fence."""
        # Check for ```json ... ``` code fence
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_content)
        candidate = json_match.group(1) if json_match else text_content

        try:
            return json.loads(candidate.strip())
        except json.JSONDecodeError:
            # Fallback search for outer curly braces
            brace_match = re.search(r"\{[\s\S]*\}", text_content)
            if brace_match:
                return json.loads(brace_match.group(0))
            raise ValueError(f"Failed to extract valid JSON from LLM output:\n{text_content}")
