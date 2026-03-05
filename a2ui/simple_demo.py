"""
A2UI Simple Demo

Quick demonstration of A2UI protocol basics.
Run with: python -m a2ui.simple_demo
"""

import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .builder import A2UIBuilder, ComponentBuilder
from .renderer import ConsoleRenderer
from .agent import SimpleA2UIAgent
from .protocol import TextVariant, Justification


console = Console()


async def main():
    console.print(Panel(
        "[bold magenta]A2UI Simple Demo[/bold magenta]\n"
        "Google's Agent-to-User Interface Protocol",
        expand=False
    ))

    # 1. Build a simple UI using the builder API
    console.print("\n[bold cyan]1. Building UI with Builder API[/bold cyan]")

    builder = A2UIBuilder()
    c = ComponentBuilder

    surface = builder.create_surface("simple_demo")
    surface.add_components(
        c.column("root", ["title", "description", "button_row"]),
        c.text("title", "Hello A2UI!", variant=TextVariant.H1),
        c.text("description", "This UI was generated using the A2UI protocol."),
        c.row("button_row", ["primary_btn", "secondary_btn"], justify=Justification.CENTER),
        c.button("primary_btn", "primary_label", "primary_action", primary=True),
        c.text("primary_label", "Primary"),
        c.button("secondary_btn", "secondary_label", "secondary_action"),
        c.text("secondary_label", "Secondary"),
    )

    # Show generated JSON
    messages = surface.to_json()
    console.print("\n[yellow]Generated A2UI JSON:[/yellow]")
    console.print(Syntax(json.dumps(messages, indent=2), "json"))

    # 2. Render the UI
    console.print("\n[bold cyan]2. Rendering with ConsoleRenderer[/bold cyan]")

    renderer = ConsoleRenderer(console)
    renderer.process_messages(surface.build_messages())
    renderer.render("simple_demo")

    # 3. Use the agent to generate UI
    console.print("\n[bold cyan]3. Agent-Generated UI[/bold cyan]")

    agent = SimpleA2UIAgent()

    queries = ["Show me a form", "Show a dashboard"]
    for query in queries:
        console.print(f"\n[green]Query:[/green] {query}")
        response = await agent.process_query(query)
        console.print(f"[yellow]Response:[/yellow] {response.text}")
        console.print(f"[dim]Generated {len(response.ui_messages)} A2UI messages[/dim]")

    console.print("\n[bold green]Done![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
