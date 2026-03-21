"""Configuration management for the shopping agent."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    anthropic_api_key: str
    ucp_base_url: str
    claude_model: str

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. "
                "Set it in .env or as an environment variable."
            )

        return cls(
            anthropic_api_key=api_key,
            ucp_base_url=os.getenv("UCP_BASE_URL", "http://localhost:8000"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        )
