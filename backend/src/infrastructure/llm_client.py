import os
import logging
from typing import Any, List, Dict, Optional
import openai

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Unified LLM Client using OpenAI-compatible API (e.g., OpenRouter).
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        """
        Initialize the LLM client.

        Args:
            api_key: API Key for the LLM provider. Defaults to OPENROUTER_API_KEY or OPENAI_API_KEY.
            base_url: Base URL for the API. Defaults to OpenRouter if not provided.
            model: Default model to use. Defaults to a sensible OpenRouter model.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = model or os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")

        if not self.api_key:
            logger.warning("No API key provided for LLMClient. LLM features may fail.")

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"LLMClient initialized with model: {self.model} via {self.base_url}")

    def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: The system instruction.
            user_prompt: The user query.
            temperature: Creativity control.
            max_tokens: Max tokens to generate.
            response_format: Optional JSON schema or valid format dict (e.g., {"type": "json_object"}).

        Returns:
            The content string from the LLM.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            logger.debug("Sending request to LLM...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                # response_format=response_format,  # Uncomment if using models that strictly support this
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Received empty response from LLM")
            
            return content

        except Exception as e:
            logger.error(f"LLM API Error: {e}")
            raise
