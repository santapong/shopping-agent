"""Claude AI shopping agent with tool-use.

Implements the agentic loop: user message -> Claude reasoning -> tool calls
-> tool results -> Claude response.
"""

from __future__ import annotations

import anthropic

from .config import Config
from .tools import TOOL_DEFINITIONS, execute_tool
from .ucp_client import UCPClient

SYSTEM_PROMPT = """\
You are a helpful AI shopping assistant powered by Google's Universal Commerce \
Protocol (UCP). You help users discover products, compare options, manage their \
shopping cart, and complete purchases.

## Your capabilities:
- Search for products across multiple merchants
- Show detailed product information
- Manage the user's shopping cart (add, remove, view items)
- Guide users through the checkout process
- Track order status

## Guidelines:
- Be friendly, concise, and helpful
- When showing search results, present them in a clear, organized way
- Proactively suggest relevant products based on user needs
- Always confirm before placing an order
- When the user wants to checkout, guide them step by step:
  1. Show cart summary
  2. Ask for shipping address
  3. Show order total and ask for confirmation
  4. Place the order
- Format prices clearly with currency symbols
- If a search returns no results, suggest alternative search terms
- Remember product IDs from search results so users can refer to items by name

## Important:
- You are shopping on behalf of the user - act as their personal shopping agent
- Always use the available tools to interact with the UCP commerce system
- Never make up product information - always use the search and detail tools
"""


class ShoppingAgent:
    """Claude-powered shopping agent with UCP tool-use."""

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.ucp_client = UCPClient(base_url=config.ucp_base_url)
        self.messages: list[dict] = []

    async def chat(self, user_message: str) -> str:
        """Process a user message and return the agent's response.

        Handles the full agentic loop including tool calls.
        """
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model=self.config.claude_model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=self.messages,
        )

        # Agentic loop: keep processing until no more tool calls
        while response.stop_reason == "tool_use":
            # Collect assistant message (may contain text + tool_use blocks)
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append(
                        {"type": "text", "text": block.text}
                    )
                elif block.type == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

            self.messages.append({"role": "assistant", "content": assistant_content})

            # Execute all tool calls and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(
                        tool_name=block.name,
                        tool_input=block.input,
                        ucp_client=self.ucp_client,
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            self.messages.append({"role": "user", "content": tool_results})

            # Continue the conversation with tool results
            response = self.client.messages.create(
                model=self.config.claude_model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.messages,
            )

        # Extract final text response
        final_text = ""
        assistant_content = []
        for block in response.content:
            if block.type == "text":
                final_text += block.text
                assistant_content.append({"type": "text", "text": block.text})

        self.messages.append({"role": "assistant", "content": assistant_content})
        return final_text

    async def close(self):
        """Clean up resources."""
        await self.ucp_client.close()
