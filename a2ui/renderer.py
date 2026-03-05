"""
A2UI Renderer - Base class and console implementation for rendering A2UI components

The renderer takes A2UI messages and renders them to a target output.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.markdown import Markdown

from .protocol import (
    A2UIServerMessage,
    A2UIClientMessage,
    CreateSurfaceMessage,
    UpdateComponentsMessage,
    UpdateDataModelMessage,
    DeleteSurfaceMessage,
    ActionEvent,
    TextVariant,
)


class A2UIRenderer(ABC):
    """Abstract base class for A2UI renderers"""

    def __init__(self):
        self._surfaces: dict[str, dict[str, Any]] = {}
        self._data_models: dict[str, dict[str, Any]] = {}
        self._action_handlers: dict[str, Callable[[ActionEvent], None]] = {}

    def process_message(self, message: A2UIServerMessage) -> None:
        """Process an incoming server message"""
        if isinstance(message, CreateSurfaceMessage):
            self._handle_create_surface(message)
        elif isinstance(message, UpdateComponentsMessage):
            self._handle_update_components(message)
        elif isinstance(message, UpdateDataModelMessage):
            self._handle_update_data_model(message)
        elif isinstance(message, DeleteSurfaceMessage):
            self._handle_delete_surface(message)

    def process_messages(self, messages: list[A2UIServerMessage]) -> None:
        """Process multiple messages"""
        for msg in messages:
            self.process_message(msg)

    def register_action_handler(self, action_name: str, handler: Callable[[ActionEvent], None]) -> None:
        """Register a handler for a specific action"""
        self._action_handlers[action_name] = handler

    def trigger_action(self, action_name: str, surface_id: str, component_id: str, context: dict[str, Any] | None = None) -> ActionEvent:
        """Trigger an action and call registered handler"""
        event = ActionEvent.create(action_name, surface_id, component_id, context)
        if action_name in self._action_handlers:
            self._action_handlers[action_name](event)
        return event

    def _handle_create_surface(self, message: CreateSurfaceMessage) -> None:
        surface_id = message.createSurface["surfaceId"]
        catalog_id = message.createSurface["catalogId"]
        self._surfaces[surface_id] = {"catalogId": catalog_id, "components": {}}
        self._data_models[surface_id] = {}
        self.on_surface_created(surface_id, catalog_id)

    def _handle_update_components(self, message: UpdateComponentsMessage) -> None:
        surface_id = message.updateComponents["surfaceId"]
        components = message.updateComponents["components"]
        if surface_id in self._surfaces:
            for comp in components:
                comp_id = comp.get("id")
                if comp_id:
                    self._surfaces[surface_id]["components"][comp_id] = comp
            self.on_components_updated(surface_id, components)

    def _handle_update_data_model(self, message: UpdateDataModelMessage) -> None:
        surface_id = message.updateDataModel["surfaceId"]
        path = message.updateDataModel.get("path", "/")
        value = message.updateDataModel.get("value")
        if surface_id not in self._data_models:
            self._data_models[surface_id] = {}
        if path == "/":
            self._data_models[surface_id] = value or {}
        else:
            self._set_path_value(self._data_models[surface_id], path, value)
        self.on_data_model_updated(surface_id, path, value)

    def _handle_delete_surface(self, message: DeleteSurfaceMessage) -> None:
        surface_id = message.deleteSurface["surfaceId"]
        if surface_id in self._surfaces:
            del self._surfaces[surface_id]
        if surface_id in self._data_models:
            del self._data_models[surface_id]
        self.on_surface_deleted(surface_id)

    def _set_path_value(self, data: dict[str, Any], path: str, value: Any) -> None:
        """Set a value at a JSON path"""
        parts = [p for p in path.split("/") if p]
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        if parts:
            if value is None:
                current.pop(parts[-1], None)
            else:
                current[parts[-1]] = value

    def resolve_binding(self, surface_id: str, binding: Any) -> Any:
        """Resolve a value that might be a path binding"""
        if isinstance(binding, dict) and "path" in binding:
            return self._get_path_value(self._data_models.get(surface_id, {}), binding["path"])
        return binding

    def _get_path_value(self, data: dict[str, Any], path: str) -> Any:
        """Get a value at a JSON path"""
        parts = [p for p in path.split("/") if p]
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def get_component(self, surface_id: str, component_id: str) -> dict[str, Any] | None:
        """Get a component by ID"""
        if surface_id in self._surfaces:
            return self._surfaces[surface_id]["components"].get(component_id)
        return None

    def get_data_model(self, surface_id: str) -> dict[str, Any]:
        """Get the data model for a surface"""
        return self._data_models.get(surface_id, {})

    @abstractmethod
    def on_surface_created(self, surface_id: str, catalog_id: str) -> None:
        """Called when a surface is created"""
        pass

    @abstractmethod
    def on_components_updated(self, surface_id: str, components: list[dict[str, Any]]) -> None:
        """Called when components are updated"""
        pass

    @abstractmethod
    def on_data_model_updated(self, surface_id: str, path: str, value: Any) -> None:
        """Called when data model is updated"""
        pass

    @abstractmethod
    def on_surface_deleted(self, surface_id: str) -> None:
        """Called when a surface is deleted"""
        pass

    @abstractmethod
    def render(self, surface_id: str) -> None:
        """Render the surface"""
        pass


class ConsoleRenderer(A2UIRenderer):
    """Console-based renderer using Rich library"""

    def __init__(self, console: Console | None = None):
        super().__init__()
        self.console = console or Console()

    def on_surface_created(self, surface_id: str, catalog_id: str) -> None:
        self.console.print(f"[green]Surface created:[/green] {surface_id}")

    def on_components_updated(self, surface_id: str, components: list[dict[str, Any]]) -> None:
        self.console.print(f"[blue]Components updated:[/blue] {len(components)} component(s)")

    def on_data_model_updated(self, surface_id: str, path: str, value: Any) -> None:
        self.console.print(f"[yellow]Data updated:[/yellow] {path}")

    def on_surface_deleted(self, surface_id: str) -> None:
        self.console.print(f"[red]Surface deleted:[/red] {surface_id}")

    def render(self, surface_id: str) -> None:
        """Render the surface to console"""
        if surface_id not in self._surfaces:
            self.console.print(f"[red]Surface not found:[/red] {surface_id}")
            return

        surface = self._surfaces[surface_id]
        components = surface["components"]

        # Find root component
        root = components.get("root")
        if not root:
            self.console.print("[red]No root component found[/red]")
            return

        # Build and render tree
        tree = Tree(f"[bold]Surface: {surface_id}[/bold]")
        self._render_component_tree(surface_id, root, tree)
        self.console.print(tree)

    def _render_component_tree(self, surface_id: str, component: dict[str, Any], tree: Tree) -> None:
        """Recursively render component tree"""
        comp_type = component.get("component", "Unknown")
        comp_id = component.get("id", "?")

        # Create label based on component type
        label = self._format_component(surface_id, component)
        branch = tree.add(label)

        # Handle children
        children = component.get("children", [])
        if isinstance(children, list):
            for child_id in children:
                child = self.get_component(surface_id, child_id)
                if child:
                    self._render_component_tree(surface_id, child, branch)

        # Handle single child
        child_id = component.get("child")
        if child_id:
            child = self.get_component(surface_id, child_id)
            if child:
                self._render_component_tree(surface_id, child, branch)

        # Handle tabs
        tabs = component.get("tabs", [])
        for tab in tabs:
            tab_branch = branch.add(f"[cyan]Tab: {tab.get('title', '?')}[/cyan]")
            tab_child = self.get_component(surface_id, tab.get("child", ""))
            if tab_child:
                self._render_component_tree(surface_id, tab_child, tab_branch)

    def _format_component(self, surface_id: str, component: dict[str, Any]) -> str:
        """Format a component for display"""
        comp_type = component.get("component", "Unknown")
        comp_id = component.get("id", "?")

        if comp_type == "Text":
            text = self.resolve_binding(surface_id, component.get("text", ""))
            variant = component.get("variant", "body")
            return f"[bold magenta]{comp_type}[/bold magenta] ({comp_id}): \"{text}\" [{variant}]"

        elif comp_type == "Button":
            action = component.get("action", {})
            action_name = action.get("name", "?")
            primary = "primary" if component.get("primary") else "secondary"
            return f"[bold green]{comp_type}[/bold green] ({comp_id}): action={action_name} [{primary}]"

        elif comp_type == "TextField":
            label = self.resolve_binding(surface_id, component.get("label", ""))
            value = self.resolve_binding(surface_id, component.get("value", ""))
            return f"[bold cyan]{comp_type}[/bold cyan] ({comp_id}): \"{label}\" = \"{value}\""

        elif comp_type == "Image":
            url = self.resolve_binding(surface_id, component.get("url", ""))
            return f"[bold yellow]{comp_type}[/bold yellow] ({comp_id}): {url[:50]}..."

        elif comp_type in ("Row", "Column", "List"):
            children = component.get("children", [])
            count = len(children) if isinstance(children, list) else "dynamic"
            return f"[bold blue]{comp_type}[/bold blue] ({comp_id}): {count} children"

        elif comp_type == "Card":
            return f"[bold white]{comp_type}[/bold white] ({comp_id})"

        elif comp_type == "CheckBox":
            label = self.resolve_binding(surface_id, component.get("label", ""))
            value = self.resolve_binding(surface_id, component.get("value", False))
            checked = "[x]" if value else "[ ]"
            return f"[bold cyan]{comp_type}[/bold cyan] ({comp_id}): [{checked}] {label}"

        elif comp_type == "ChoicePicker":
            label = self.resolve_binding(surface_id, component.get("label", ""))
            options = component.get("options", [])
            return f"[bold cyan]{comp_type}[/bold cyan] ({comp_id}): {label} ({len(options)} options)"

        elif comp_type == "Slider":
            label = self.resolve_binding(surface_id, component.get("label", ""))
            value = self.resolve_binding(surface_id, component.get("value", 0))
            return f"[bold cyan]{comp_type}[/bold cyan] ({comp_id}): {label} = {value}"

        elif comp_type == "Divider":
            axis = component.get("axis", "horizontal")
            return f"[dim]{comp_type}[/dim] ({comp_id}): {axis}"

        else:
            return f"[bold]{comp_type}[/bold] ({comp_id})"

    def render_json(self, surface_id: str) -> None:
        """Render the surface as formatted JSON"""
        if surface_id not in self._surfaces:
            self.console.print(f"[red]Surface not found:[/red] {surface_id}")
            return

        surface = self._surfaces[surface_id]
        data_model = self._data_models.get(surface_id, {})

        self.console.print(Panel(
            json.dumps({"components": surface["components"], "dataModel": data_model}, indent=2),
            title=f"Surface: {surface_id}",
            border_style="blue"
        ))

    def render_data_model(self, surface_id: str) -> None:
        """Render just the data model"""
        data_model = self._data_models.get(surface_id, {})
        self.console.print(Panel(
            json.dumps(data_model, indent=2),
            title=f"Data Model: {surface_id}",
            border_style="yellow"
        ))
