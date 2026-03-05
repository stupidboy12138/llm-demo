"""
A2UI (Agent-to-User Interface) Protocol Implementation

Google's A2UI protocol enables AI agents to generate rich, interactive UIs
through declarative JSON format. This implementation follows the v0.9 specification.

Key concepts:
- Security-first: Declarative data, not executable code
- LLM-friendly: Flat component list with ID references
- Framework-agnostic: Same JSON works across different renderers
"""

from .protocol import (
    # Message types
    CreateSurfaceMessage,
    UpdateComponentsMessage,
    UpdateDataModelMessage,
    DeleteSurfaceMessage,
    A2UIServerMessage,
    # Client messages
    ActionEvent,
    ErrorEvent,
    CapabilitiesEvent,
    A2UIClientMessage,
    # Component types
    Component,
    TextComponent,
    ImageComponent,
    IconComponent,
    ButtonComponent,
    TextFieldComponent,
    CheckBoxComponent,
    ChoicePickerComponent,
    SliderComponent,
    DateTimeInputComponent,
    RowComponent,
    ColumnComponent,
    ListComponent,
    CardComponent,
    TabsComponent,
    DividerComponent,
    ModalComponent,
    # Dynamic types
    DynamicString,
    DynamicNumber,
    DynamicBoolean,
    DynamicValue,
    PathBinding,
    FunctionCall,
    # Action types
    Action,
    ActionContext,
    # Enums
    TextVariant,
    ImageFit,
    ImageVariant,
    TextFieldVariant,
    ChoicePickerVariant,
    Alignment,
    Justification,
    ListDirection,
    DividerAxis,
)

from .builder import (
    A2UIBuilder,
    SurfaceBuilder,
    ComponentBuilder,
)

from .renderer import (
    A2UIRenderer,
    ConsoleRenderer,
)

from .agent import (
    A2UIAgent,
    A2UIAgentConfig,
)

__version__ = "0.9.0"
__all__ = [
    # Message types
    "CreateSurfaceMessage",
    "UpdateComponentsMessage",
    "UpdateDataModelMessage",
    "DeleteSurfaceMessage",
    "A2UIServerMessage",
    "ActionEvent",
    "ErrorEvent",
    "CapabilitiesEvent",
    "A2UIClientMessage",
    # Components
    "Component",
    "TextComponent",
    "ImageComponent",
    "IconComponent",
    "ButtonComponent",
    "TextFieldComponent",
    "CheckBoxComponent",
    "ChoicePickerComponent",
    "SliderComponent",
    "DateTimeInputComponent",
    "RowComponent",
    "ColumnComponent",
    "ListComponent",
    "CardComponent",
    "TabsComponent",
    "DividerComponent",
    "ModalComponent",
    # Dynamic types
    "DynamicString",
    "DynamicNumber",
    "DynamicBoolean",
    "DynamicValue",
    "PathBinding",
    "FunctionCall",
    # Action types
    "Action",
    "ActionContext",
    # Enums
    "TextVariant",
    "ImageFit",
    "ImageVariant",
    "TextFieldVariant",
    "ChoicePickerVariant",
    "Alignment",
    "Justification",
    "ListDirection",
    "DividerAxis",
    # Builder
    "A2UIBuilder",
    "SurfaceBuilder",
    "ComponentBuilder",
    # Renderer
    "A2UIRenderer",
    "ConsoleRenderer",
    # Agent
    "A2UIAgent",
    "A2UIAgentConfig",
]
