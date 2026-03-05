"""
A2UI Protocol Demo

Demonstrates the A2UI (Agent-to-User Interface) protocol implementation.
Based on Google's A2UI specification v0.9: https://github.com/google/A2UI

Run with: python -m a2ui.demo
"""

import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from a2ui import CreateSurfaceMessage, UpdateComponentsMessage, UpdateDataModelMessage, ActionEvent, A2UIBuilder, \
    ComponentBuilder, TextVariant, Alignment, Justification, ConsoleRenderer
from a2ui.agent import SimpleA2UIAgent

console = Console()


def demo_protocol_basics():
    """Demonstrate basic A2UI protocol message types"""
    console.print(Panel("[bold cyan]A2UI Protocol Basics[/bold cyan]", expand=False))

    # Create surface message
    create_msg = CreateSurfaceMessage.create("demo_surface_1", "https://a2ui.dev/catalog/standard")
    console.print("\n[yellow]1. CreateSurface Message:[/yellow]")
    console.print(Syntax(json.dumps(create_msg.model_dump(), indent=2), "json"))

    # Update components message
    components = [
        {"id": "root", "component": "Column", "children": ["title", "button"]},
        {"id": "title", "component": "Text", "text": "Hello A2UI!", "variant": "h1"},
        {"id": "button", "component": "Button", "child": "btn_label", "action": {"name": "click"}},
        {"id": "btn_label", "component": "Text", "text": "Click Me"},
    ]
    update_msg = UpdateComponentsMessage.create("demo_surface_1", components)
    console.print("\n[yellow]2. UpdateComponents Message:[/yellow]")
    console.print(Syntax(json.dumps(update_msg.model_dump(), indent=2), "json"))

    # Update data model message
    data_msg = UpdateDataModelMessage.create("demo_surface_1", {"user": {"name": "Alice"}}, "/")
    console.print("\n[yellow]3. UpdateDataModel Message:[/yellow]")
    console.print(Syntax(json.dumps(data_msg.model_dump(), indent=2), "json"))

    # Action event (client to server)
    action = ActionEvent.create("click", "demo_surface_1", "button", {"clicked": True})
    console.print("\n[yellow]4. ActionEvent (Client → Server):[/yellow]")
    console.print(Syntax(json.dumps(action.model_dump(), indent=2), "json"))


def demo_builder_api():
    """Demonstrate the fluent builder API"""
    console.print(Panel("[bold cyan]A2UI Builder API[/bold cyan]", expand=False))

    builder = A2UIBuilder()
    c = ComponentBuilder

    # Build a contact form surface
    surface = builder.create_surface("contact_form")

    surface.add_components(
        c.column("root", ["header", "form_fields", "submit_row"], align=Alignment.STRETCH),
        c.text("header", "Contact Us", variant=TextVariant.H1),
        c.column("form_fields", ["name_field", "email_field", "message_field"]),
        c.text_field("name_field", "Your Name", value=c.path("/form/name")),
        c.text_field("email_field", "Email", value=c.path("/form/email"),
                    checks=[c.check_rule("email", "Invalid email format")]),
        c.text_field("message_field", "Message", value=c.path("/form/message"), variant="longText"),
        c.row("submit_row", ["cancel_btn", "submit_btn"], justify=Justification.END),
        c.button("cancel_btn", "cancel_label", "cancel"),
        c.text("cancel_label", "Cancel"),
        c.button("submit_btn", "submit_label", "submit",
                context=[("name", c.path("/form/name")), ("email", c.path("/form/email"))],
                primary=True),
        c.text("submit_label", "Submit"),
    )

    surface.set_root_data({
        "form": {"name": "", "email": "", "message": ""}
    })

    messages = surface.to_json()
    console.print("\n[yellow]Generated A2UI Messages:[/yellow]")
    console.print(Syntax(json.dumps(messages, indent=2), "json"))


def demo_renderer():
    """Demonstrate the console renderer"""
    console.print(Panel("[bold cyan]A2UI Console Renderer[/bold cyan]", expand=False))

    renderer = ConsoleRenderer(console)
    c = ComponentBuilder

    # Build a simple UI
    builder = A2UIBuilder()
    surface = builder.create_surface("renderer_demo")

    surface.add_components(
        c.column("root", ["title", "content_row", "footer"]),
        c.text("title", "Renderer Demo", variant=TextVariant.H1),
        c.row("content_row", ["left_panel", "right_panel"]),
        c.card("left_panel", "left_content"),
        c.column("left_content", ["left_title", "left_text"]),
        c.text("left_title", "Left Panel", variant=TextVariant.H3),
        c.text("left_text", "This is the left panel content"),
        c.card("right_panel", "right_content"),
        c.column("right_content", ["right_title", "right_text", "action_btn"]),
        c.text("right_title", "Right Panel", variant=TextVariant.H3),
        c.text("right_text", "This is the right panel content"),
        c.button("action_btn", "action_label", "do_action", primary=True),
        c.text("action_label", "Take Action"),
        c.text("footer", "(c) 2025 A2UI Demo", variant=TextVariant.CAPTION),
    )

    # Process messages through renderer
    messages = surface.build_messages()
    renderer.process_messages(messages)

    console.print("\n[yellow]Rendered Component Tree:[/yellow]")
    renderer.render("renderer_demo")


async def demo_agent():
    """Demonstrate the A2UI agent"""
    console.print(Panel("[bold cyan]A2UI Agent Demo[/bold cyan]", expand=False))

    agent = SimpleA2UIAgent()
    renderer = ConsoleRenderer(console)

    # Test different queries
    queries = [
        "Show me a contact form",
        "Display a list of items",
        "Show a profile card",
        "Open the dashboard",
    ]

    for query in queries:
        console.print(f"\n[bold green]Query:[/bold green] {query}")
        response = await agent.process_query(query)

        console.print(f"[yellow]Agent Response:[/yellow] {response.text}")

        if response.ui_messages:
            # Process UI messages
            for msg_dict in response.ui_messages:
                if "createSurface" in msg_dict:
                    msg = CreateSurfaceMessage(**msg_dict)
                elif "updateComponents" in msg_dict:
                    msg = UpdateComponentsMessage(**msg_dict)
                elif "updateDataModel" in msg_dict:
                    msg = UpdateDataModelMessage(**msg_dict)
                else:
                    continue
                renderer.process_message(msg)

            # Get surface ID from first message
            surface_id = response.ui_messages[0].get("createSurface", {}).get("surfaceId")
            if surface_id:
                console.print(f"\n[cyan]Component Tree for {surface_id}:[/cyan]")
                renderer.render(surface_id)

        console.print("\n" + "─" * 60)


def demo_data_binding():
    """Demonstrate data binding with path references"""
    console.print(Panel("[bold cyan]A2UI Data Binding[/bold cyan]", expand=False))

    renderer = ConsoleRenderer(console)
    c = ComponentBuilder

    builder = A2UIBuilder()
    surface = builder.create_surface("data_binding_demo")

    surface.add_components(
        c.column("root", ["user_card"]),
        c.card("user_card", "user_content"),
        c.column("user_content", ["user_name", "user_email", "user_role"]),
        c.text("user_name", c.path("/user/name"), variant=TextVariant.H2),
        c.text("user_email", c.path("/user/email")),
        c.text("user_role", c.path("/user/role"), variant=TextVariant.CAPTION),
    )

    # Set initial data
    surface.set_root_data({
        "user": {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "Administrator"
        }
    })

    renderer.process_messages(surface.build_messages())

    console.print("\n[yellow]Initial State:[/yellow]")
    renderer.render("data_binding_demo")
    renderer.render_data_model("data_binding_demo")

    # Update data
    update_msg = UpdateDataModelMessage.create("data_binding_demo", "Jane Smith", "/user/name")
    renderer.process_message(update_msg)

    console.print("\n[yellow]After Updating Name:[/yellow]")
    renderer.render_data_model("data_binding_demo")


def demo_action_handling():
    """Demonstrate action handling"""
    console.print(Panel("[bold cyan]A2UI Action Handling[/bold cyan]", expand=False))

    renderer = ConsoleRenderer(console)
    actions_received: list[dict] = []

    # Register action handler
    def handle_submit(event: ActionEvent):
        actions_received.append(event.action)
        console.print(f"[green]Action received:[/green] {event.action['name']}")
        console.print(f"  Context: {event.action['context']}")

    renderer.register_action_handler("submit_form", handle_submit)

    # Trigger action
    console.print("\n[yellow]Triggering action...[/yellow]")
    event = renderer.trigger_action(
        "submit_form",
        "demo_surface",
        "submit_button",
        {"field1": "value1", "field2": "value2"}
    )

    console.print(f"\n[yellow]Action Event JSON:[/yellow]")
    console.print(Syntax(json.dumps(event.model_dump(), indent=2), "json"))


async def main():
    """Run all demos"""
    console.print(Panel(
        "[bold magenta]Google A2UI Protocol Demo[/bold magenta]\n"
        "Agent-to-User Interface Protocol v0.9\n"
        "https://github.com/google/A2UI",
        expand=False
    ))

    demos = [
        ("Protocol Basics", demo_protocol_basics),
        ("Builder API", demo_builder_api),
        ("Console Renderer", demo_renderer),
        ("Data Binding", demo_data_binding),
        ("Action Handling", demo_action_handling),
        ("Agent Demo", demo_agent),
    ]

    for name, demo_func in demos:
        console.print(f"\n{'=' * 60}")
        if asyncio.iscoroutinefunction(demo_func):
            await demo_func()
        else:
            demo_func()
        console.print()

    console.print(Panel(
        "[bold green]Demo Complete![/bold green]\n\n"
        "Key A2UI Concepts Demonstrated:\n"
        "- Server-to-Client messages (CreateSurface, UpdateComponents, UpdateDataModel)\n"
        "- Client-to-Server events (ActionEvent)\n"
        "- Component types (Text, Button, TextField, Row, Column, Card, etc.)\n"
        "- Data binding with path references\n"
        "- Fluent builder API\n"
        "- Console rendering\n"
        "- Agent-based UI generation",
        expand=False
    ))


if __name__ == "__main__":
    asyncio.run(main())
