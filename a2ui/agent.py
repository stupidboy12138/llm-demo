"""
A2UI Agent - AI agent that generates A2UI responses

Provides a base class for building agents that can generate rich UI responses
using the A2UI protocol.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from dataclasses import dataclass, field
from pydantic import BaseModel

from .protocol import A2UIServerMessage
from .builder import A2UIBuilder, SurfaceBuilder, ComponentBuilder


@dataclass
class A2UIAgentConfig:
    """Configuration for A2UI agent"""
    agent_id: str
    name: str
    description: str = ""
    catalog_id: str = "https://a2ui.dev/catalog/standard"
    supported_actions: list[str] = field(default_factory=list)


class A2UIAgentResponse(BaseModel):
    """Response from an A2UI agent"""
    text: str | None = None
    ui_messages: list[dict[str, Any]] = []
    is_complete: bool = True
    error: str | None = None


class A2UIAgent(ABC):
    """Base class for A2UI-capable agents"""

    def __init__(self, config: A2UIAgentConfig):
        self.config = config
        self._surface_counter = 0

    def _generate_surface_id(self) -> str:
        """Generate a unique surface ID"""
        self._surface_counter += 1
        return f"{self.config.agent_id}_surface_{self._surface_counter}"

    def create_builder(self) -> A2UIBuilder:
        """Create a new A2UI builder"""
        return A2UIBuilder()

    def create_surface(self, surface_id: str | None = None) -> SurfaceBuilder:
        """Create a new surface builder"""
        builder = A2UIBuilder()
        sid = surface_id or self._generate_surface_id()
        return builder.create_surface(sid, self.config.catalog_id)

    @staticmethod
    def component() -> type[ComponentBuilder]:
        """Access component builder"""
        return ComponentBuilder

    @abstractmethod
    async def process_query(self, query: str, context: dict[str, Any] | None = None) -> A2UIAgentResponse:
        """Process a user query and return a response with optional UI"""
        pass

    async def process_action(self, action_name: str, context: dict[str, Any]) -> A2UIAgentResponse:
        """Process a user action from the UI"""
        return A2UIAgentResponse(
            text=f"Action '{action_name}' received",
            is_complete=True
        )

    async def stream_response(self, query: str, context: dict[str, Any] | None = None) -> AsyncIterator[A2UIAgentResponse]:
        """Stream responses for a query"""
        response = await self.process_query(query, context)
        yield response


class SimpleA2UIAgent(A2UIAgent):
    """Simple A2UI agent for demonstration purposes"""

    def __init__(self, config: A2UIAgentConfig | None = None):
        if config is None:
            config = A2UIAgentConfig(
                agent_id="simple_agent",
                name="Simple A2UI Agent",
                description="A simple agent that demonstrates A2UI capabilities"
            )
        super().__init__(config)

    async def process_query(self, query: str, context: dict[str, Any] | None = None) -> A2UIAgentResponse:
        """Process query and generate appropriate UI"""
        query_lower = query.lower()

        # Handle different query types
        if "form" in query_lower or "contact" in query_lower:
            return self._create_contact_form()
        elif "list" in query_lower or "items" in query_lower:
            return self._create_item_list()
        elif "card" in query_lower or "profile" in query_lower:
            return self._create_profile_card()
        elif "dashboard" in query_lower:
            return self._create_dashboard()
        else:
            return self._create_welcome_ui(query)

    def _create_welcome_ui(self, query: str) -> A2UIAgentResponse:
        """Create a welcome UI"""
        surface = self.create_surface()
        c = self.component()

        surface.add_components(
            c.column("root", ["title", "subtitle", "actions_row"]),
            c.text("title", "Welcome to A2UI Demo", variant="h1"),
            c.text("subtitle", f"You said: {query}", variant="body"),
            c.row("actions_row", ["help_btn", "explore_btn"], justify="center"),
            c.button("help_btn", "help_label", "show_help"),
            c.text("help_label", "Get Help"),
            c.button("explore_btn", "explore_label", "explore", primary=True),
            c.text("explore_label", "Explore Features"),
        )

        return A2UIAgentResponse(
            text="Here's a welcome screen. Try asking for 'form', 'list', 'card', or 'dashboard'.",
            ui_messages=surface.to_json()
        )

    def _create_contact_form(self) -> A2UIAgentResponse:
        """Create a contact form UI"""
        surface = self.create_surface()
        c = self.component()

        surface.add_components(
            c.column("root", ["form_title", "name_field", "email_field", "message_field", "submit_btn"]),
            c.text("form_title", "Contact Form", variant="h2"),
            c.text_field("name_field", "Your Name", value=c.path("/contact/name"), variant="shortText"),
            c.text_field("email_field", "Email Address", value=c.path("/contact/email"), variant="shortText",
                        checks=[c.check_rule("email", "Please enter a valid email")]),
            c.text_field("message_field", "Message", value=c.path("/contact/message"), variant="longText"),
            c.button("submit_btn", "submit_label", "submit_contact",
                    context=[("name", c.path("/contact/name")), ("email", c.path("/contact/email"))],
                    primary=True),
            c.text("submit_label", "Send Message"),
        )

        surface.set_root_data({
            "contact": {
                "name": "",
                "email": "",
                "message": ""
            }
        })

        return A2UIAgentResponse(
            text="Here's a contact form. Fill in your details and submit.",
            ui_messages=surface.to_json()
        )

    def _create_item_list(self) -> A2UIAgentResponse:
        """Create an item list UI"""
        surface = self.create_surface()
        c = self.component()

        surface.add_components(
            c.column("root", ["list_title", "item_list"]),
            c.text("list_title", "Available Items", variant="h2"),
            c.list_view("item_list", ["item_1", "item_2", "item_3"]),
            # Item 1
            c.card("item_1", "item_1_content"),
            c.row("item_1_content", ["item_1_info", "item_1_action"]),
            c.column("item_1_info", ["item_1_name", "item_1_desc"]),
            c.text("item_1_name", c.path("/items/0/name"), variant="h4"),
            c.text("item_1_desc", c.path("/items/0/description")),
            c.button("item_1_action", "select_label_1", "select_item", context=[("id", "1")]),
            c.text("select_label_1", "Select"),
            # Item 2
            c.card("item_2", "item_2_content"),
            c.row("item_2_content", ["item_2_info", "item_2_action"]),
            c.column("item_2_info", ["item_2_name", "item_2_desc"]),
            c.text("item_2_name", c.path("/items/1/name"), variant="h4"),
            c.text("item_2_desc", c.path("/items/1/description")),
            c.button("item_2_action", "select_label_2", "select_item", context=[("id", "2")]),
            c.text("select_label_2", "Select"),
            # Item 3
            c.card("item_3", "item_3_content"),
            c.row("item_3_content", ["item_3_info", "item_3_action"]),
            c.column("item_3_info", ["item_3_name", "item_3_desc"]),
            c.text("item_3_name", c.path("/items/2/name"), variant="h4"),
            c.text("item_3_desc", c.path("/items/2/description")),
            c.button("item_3_action", "select_label_3", "select_item", context=[("id", "3")]),
            c.text("select_label_3", "Select"),
        )

        surface.set_root_data({
            "items": [
                {"name": "Product A", "description": "High-quality product with great features"},
                {"name": "Product B", "description": "Budget-friendly option for everyday use"},
                {"name": "Product C", "description": "Premium choice with advanced capabilities"},
            ]
        })

        return A2UIAgentResponse(
            text="Here's a list of items. Click 'Select' to choose one.",
            ui_messages=surface.to_json()
        )

    def _create_profile_card(self) -> A2UIAgentResponse:
        """Create a profile card UI"""
        surface = self.create_surface()
        c = self.component()

        surface.add_components(
            c.column("root", ["profile_card"]),
            c.card("profile_card", "profile_content"),
            c.column("profile_content", ["avatar", "user_name", "user_bio", "stats_row", "action_row"]),
            c.image("avatar", c.path("/user/avatar"), variant="avatar"),
            c.text("user_name", c.path("/user/name"), variant="h3"),
            c.text("user_bio", c.path("/user/bio")),
            c.row("stats_row", ["followers_stat", "following_stat", "posts_stat"], justify="spaceAround"),
            c.column("followers_stat", ["followers_count", "followers_label"]),
            c.text("followers_count", c.path("/user/followers"), variant="h4"),
            c.text("followers_label", "Followers", variant="caption"),
            c.column("following_stat", ["following_count", "following_label"]),
            c.text("following_count", c.path("/user/following"), variant="h4"),
            c.text("following_label", "Following", variant="caption"),
            c.column("posts_stat", ["posts_count", "posts_label"]),
            c.text("posts_count", c.path("/user/posts"), variant="h4"),
            c.text("posts_label", "Posts", variant="caption"),
            c.row("action_row", ["follow_btn", "message_btn"], justify="center"),
            c.button("follow_btn", "follow_label", "follow_user", primary=True),
            c.text("follow_label", "Follow"),
            c.button("message_btn", "message_label", "message_user"),
            c.text("message_label", "Message"),
        )

        surface.set_root_data({
            "user": {
                "name": "Jane Developer",
                "bio": "Full-stack developer passionate about AI and UI/UX",
                "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Jane",
                "followers": "1.2K",
                "following": "342",
                "posts": "89"
            }
        })

        return A2UIAgentResponse(
            text="Here's a user profile card.",
            ui_messages=surface.to_json()
        )

    def _create_dashboard(self) -> A2UIAgentResponse:
        """Create a dashboard UI with tabs"""
        surface = self.create_surface()
        c = self.component()

        surface.add_components(
            c.column("root", ["dash_title", "dash_tabs"]),
            c.text("dash_title", "Dashboard", variant="h1"),
            c.tabs("dash_tabs", [("Overview", "overview_tab"), ("Settings", "settings_tab")]),
            # Overview tab
            c.column("overview_tab", ["stats_section", "chart_placeholder"]),
            c.row("stats_section", ["stat_1", "stat_2", "stat_3"], justify="spaceAround"),
            c.card("stat_1", "stat_1_content"),
            c.column("stat_1_content", ["stat_1_value", "stat_1_label"]),
            c.text("stat_1_value", c.path("/stats/users"), variant="h2"),
            c.text("stat_1_label", "Total Users", variant="caption"),
            c.card("stat_2", "stat_2_content"),
            c.column("stat_2_content", ["stat_2_value", "stat_2_label"]),
            c.text("stat_2_value", c.path("/stats/revenue"), variant="h2"),
            c.text("stat_2_label", "Revenue", variant="caption"),
            c.card("stat_3", "stat_3_content"),
            c.column("stat_3_content", ["stat_3_value", "stat_3_label"]),
            c.text("stat_3_value", c.path("/stats/orders"), variant="h2"),
            c.text("stat_3_label", "Orders", variant="caption"),
            c.text("chart_placeholder", "[Chart would render here]", variant="body"),
            # Settings tab
            c.column("settings_tab", ["notifications_setting", "theme_setting", "save_btn"]),
            c.checkbox("notifications_setting", "Enable Notifications", c.path("/settings/notifications")),
            c.choice_picker("theme_setting",
                          [("Light", "light"), ("Dark", "dark"), ("System", "system")],
                          ["light"], variant="mutuallyExclusive", label="Theme"),
            c.button("save_btn", "save_label", "save_settings", primary=True),
            c.text("save_label", "Save Settings"),
        )

        surface.set_root_data({
            "stats": {
                "users": "12,543",
                "revenue": "$45.2K",
                "orders": "1,234"
            },
            "settings": {
                "notifications": True,
                "theme": "light"
            }
        })

        return A2UIAgentResponse(
            text="Here's your dashboard with overview and settings tabs.",
            ui_messages=surface.to_json()
        )

    async def process_action(self, action_name: str, context: dict[str, Any]) -> A2UIAgentResponse:
        """Handle actions from the UI"""
        if action_name == "submit_contact":
            name = context.get("name", "Unknown")
            email = context.get("email", "")
            return A2UIAgentResponse(
                text=f"Thank you {name}! We received your message and will contact you at {email}.",
                is_complete=True
            )
        elif action_name == "select_item":
            item_id = context.get("id", "?")
            return A2UIAgentResponse(
                text=f"You selected item #{item_id}. Processing your selection...",
                is_complete=True
            )
        elif action_name == "follow_user":
            return A2UIAgentResponse(text="You are now following this user!", is_complete=True)
        elif action_name == "save_settings":
            return A2UIAgentResponse(text="Settings saved successfully!", is_complete=True)
        else:
            return await super().process_action(action_name, context)
