"""CLI entry point for the AI Shopping Agent.

Run with: python -m shopping_agent.main
"""

from __future__ import annotations

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .agent import ShoppingAgent
from .config import Config

console = Console()

WELCOME_BANNER = """\
[bold cyan]AI Shopping Agent[/bold cyan] powered by [bold]Google UCP[/bold] + [bold]Claude AI[/bold]

I can help you:
  [green]•[/green] Search for products across merchants
  [green]•[/green] Compare prices and features
  [green]•[/green] Manage your shopping cart
  [green]•[/green] Complete purchases with UCP checkout

Type [bold yellow]help[/bold yellow] for commands or just tell me what you're looking for!
Type [bold yellow]quit[/bold yellow] to exit.
"""

HELP_TEXT = """\
[bold]Commands:[/bold]
  [yellow]help[/yellow]    - Show this help message
  [yellow]cart[/yellow]    - View your shopping cart
  [yellow]orders[/yellow]  - List your orders
  [yellow]clear[/yellow]   - Clear conversation history
  [yellow]quit[/yellow]    - Exit the agent

[bold]Example queries:[/bold]
  "Find me some wireless headphones under $300"
  "Show me running shoes"
  "Add the Sony headphones to my cart"
  "I want to checkout"
  "What's the status of my order?"
"""


async def run_agent():
    """Main agent loop."""
    try:
        config = Config.load()
    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        console.print("Copy .env.example to .env and set your ANTHROPIC_API_KEY.")
        sys.exit(1)

    agent = ShoppingAgent(config)

    console.print()
    console.print(Panel(WELCOME_BANNER, title="🛒 Shopping Agent", border_style="cyan"))
    console.print()

    try:
        while True:
            try:
                user_input = console.input("[bold green]You:[/bold green] ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            lower = user_input.lower()
            if lower in ("quit", "exit", "q"):
                console.print("\n[cyan]Thanks for shopping! Goodbye.[/cyan]")
                break
            elif lower == "help":
                console.print(Panel(HELP_TEXT, title="Help", border_style="yellow"))
                continue
            elif lower == "clear":
                agent.messages.clear()
                console.print("[dim]Conversation cleared.[/dim]")
                continue

            # Shortcuts that go through the agent
            if lower == "cart":
                user_input = "Show me my shopping cart"
            elif lower == "orders":
                user_input = "Show me my orders"

            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                try:
                    response = await agent.chat(user_input)
                except Exception as e:
                    console.print(f"\n[bold red]Error:[/bold red] {e}")
                    console.print("[dim]Make sure the mock server is running: python -m shopping_agent.mock_server[/dim]")
                    continue

            console.print()
            assistant_label = Text("Agent: ", style="bold cyan")
            console.print(assistant_label, end="")
            console.print(response)
            console.print()

    finally:
        await agent.close()


def main():
    """Entry point."""
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
