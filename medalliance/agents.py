import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    import anthropic
except Exception:  # pragma: no cover
    anthropic = None


class ClaudeAgent:
    """Thin wrapper around Anthropic Claude for layer-level decisions."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
        self.client = None
        if self.api_key and anthropic is not None:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def _safe_text(self, prompt: str) -> str:
        if not self.client:
            return "AI processing skipped because no Claude API key is configured."

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text_blocks = []
            for block in message.content:
                if getattr(block, "type", None) == "text":
                    text_blocks.append(block.text)
            return "\n".join(text_blocks) if text_blocks else str(message)
        except Exception as exc:  # pragma: no cover
            return f"Claude request failed: {exc}"

    def bronze_agent(self, file_name: str) -> str:
        return self._safe_text(
            f"Review the raw CSV file '{file_name}' and explain the ingestion checks needed before it enters the bronze layer."
        )

    def silver_agent(self, file_name: str) -> str:
        return self._safe_text(
            f"Review the bronze CSV file '{file_name}' and explain how to clean, standardize, and deduplicate records for the silver layer."
        )

    def gold_agent(self, file_name: str) -> str:
        return self._safe_text(
            f"Review the silver CSV file '{file_name}' and explain how to build a curated gold-layer dataset for analytics and reporting."
        )
