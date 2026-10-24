"""LLM provider abstraction with Groq and Google Gemini fallback integrations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Safemate Safety Assistant, an empathetic, supportive, and privacy-first guide for a women's safety platform.
Your objective:
1. Help the user understand their practical safety options for online harassment, blackmail, extortion, non-consensual image sharing, fake accounts, or physical stalking.
2. Maintain a calm, respectful, non-alarmist, and completely non-judgemental tone.
3. NEVER ask the user to describe explicit intimate acts or upload intimate photos/videos.
4. NEVER ask for passwords, OTPs, or authentication secrets.
5. NEVER suggest confronting an aggressive harasser, paying extortion, hacking accounts, or vigilante retaliation.
6. For immediate physical danger, always emphasize calling emergency services (112 / 181 in India).
7. For cybercrimes in India, recommend the official portal (https://cybercrime.gov.in/) and helpline 1930 for financial cyber fraud.
8. Clearly state that your advice is general safety and legal information, not formal legal counsel.
9. Keep answers concise, structured (bulleted or numbered steps where applicable), and practical. Do not overwhelm the user with long legal jargon."""


class BaseLLMProvider(ABC):
    """Abstract base class for optional conversational LLM providers."""

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Whether the provider has necessary API credentials."""
        pass

    @abstractmethod
    async def generate_response(self, user_query: str) -> Optional[str]:
        """Generate response text or return None if provider fails/unavailable."""
        pass


class GroqLLMProvider(BaseLLMProvider):
    """Groq Cloud API integration using ultra-fast LLaMA models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
    ) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.timeout = timeout
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_response(self, user_query: str) -> Optional[str]:
        if not self.is_configured:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query[:1000]},
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(self.api_url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        content = choices[0]["message"].get("content", "").strip()
                        if content:
                            return content
                else:
                    logger.warning(
                        f"Groq API returned HTTP {res.status_code}: {res.text[:200]}"
                    )
                    return None
        except httpx.TimeoutException:
            logger.warning("Groq API request timed out; attempting fallback.")
            return None
        except Exception as e:
            logger.warning(f"Groq API call failed: {type(e).__name__}: {e}; attempting fallback.")
            return None

        return None


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini REST API integration using Gemini 1.5 Flash."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
    ) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_response(self, user_query: str) -> Optional[str]:
        if not self.is_configured:
            return None

        api_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_query[:1000]}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 600,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(api_url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            content = parts[0]["text"].strip()
                            if content:
                                return content
                else:
                    logger.warning(
                        f"Gemini API returned HTTP {res.status_code}: {res.text[:200]}"
                    )
                    return None
        except httpx.TimeoutException:
            logger.warning("Gemini API request timed out; falling back to curated guidance.")
            return None
        except Exception as e:
            logger.warning(f"Gemini API call failed: {type(e).__name__}: {e}; falling back.")
            return None

        return None


class CascadingLLMProvider(BaseLLMProvider):
    """Cascading LLM provider: tries primary (Groq) then falls back to secondary (Gemini)."""

    def __init__(self, providers: Optional[List[BaseLLMProvider]] = None) -> None:
        self.providers = providers or [GroqLLMProvider(), GeminiLLMProvider()]

    @property
    def is_configured(self) -> bool:
        return any(p.is_configured for p in self.providers)

    async def generate_response(self, user_query: str) -> Optional[str]:
        for idx, provider in enumerate(self.providers):
            if provider.is_configured:
                provider_name = type(provider).__name__
                try:
                    res = await provider.generate_response(user_query)
                    if res:
                        return res
                    logger.info(f"{provider_name} returned no response; cascading to next provider.")
                except Exception as e:
                    logger.warning(f"{provider_name} failed with {type(e).__name__}: {e}; cascading.")
        return None


def get_llm_provider() -> CascadingLLMProvider:
    """Factory creating cascading Groq -> Gemini LLM provider."""
    return CascadingLLMProvider()
