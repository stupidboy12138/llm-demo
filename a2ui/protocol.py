"""
A2UI Protocol Types - v0.9 Specification

Defines all message types, components, and data structures for the A2UI protocol.
Based on https://github.com/google/A2UI specification/0.9
"""

from enum import Enum
from typing import Any, Union
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class TextVariant(str, Enum):
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    CAPTION = "caption"
    BODY = "body"


class ImageFit(str, Enum):
    CONTAIN = "contain"
    COVER = "cover"
    FILL = "fill"
    NONE = "none"
    SCALE_DOWN = "scale-down"


class ImageVariant(str, Enum):
    ICON = "icon"
    AVATAR = "avatar"
    SMALL_FEATURE = "smallFeature"
    MEDIUM_FEATURE = "mediumFeature"
    LARGE_FEATURE = "largeFeature"
    HEADER = "header"


class TextFieldVariant(str, Enum):
    SHORT_TEXT = "shortText"
    LONG_TEXT = "longText"
    NUMBER = "number"
    OBSCURED = "obscured"


class ChoicePickerVariant(str, Enum):
    MULTIPLE_SELECTION = "multipleSelection"
    MUTUALLY_EXCLUSIVE = "mutuallyExclusive"


class Alignment(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class Justification(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "spaceBetween"
    SPACE_AROUND = "spaceAround"
    SPACE_EVENLY = "spaceEvenly"
    STRETCH = "stretch"


class ListDirection(str, Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class DividerAxis(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


# =============================================================================
# Dynamic Types - Values that can be literal, path binding, or function call
# =============================================================================

class PathBinding(BaseModel):
    """Reference to a value in the data model"""
    path: str


class FunctionCall(BaseModel):
    """Client-side function invocation"""
    call: str
    args: dict[str, Any] = Field(default_factory=dict)
    returnType: str = "boolean"  # string, number, boolean, array, object, any


# Dynamic types can be literal values, path bindings, or function calls
DynamicString = Union[str, PathBinding, FunctionCall]
DynamicNumber = Union[int, float, PathBinding, FunctionCall]
DynamicBoolean = Union[bool, PathBinding, FunctionCall]
DynamicValue = Union[str, int, float, bool, PathBinding, FunctionCall]


# =============================================================================
# Action Types
# =============================================================================

class ActionContext(BaseModel):
    """Key-value pair for action context"""
    key: str
    value: DynamicValue


class Action(BaseModel):
    """Action triggered by user interaction"""
    name: str
    context: list[ActionContext] = Field(default_factory=list)


# =============================================================================
# Check Rules for Validation
# =============================================================================

class CheckRule(BaseModel):
    """Validation rule for input components"""
    call: str  # Function name like "email", "required", "minLength"
    args: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


# =============================================================================
# Child List - Static or Dynamic
# =============================================================================

class DynamicChildList(BaseModel):
    """Dynamic children generated from data model"""
    componentId: str
    path: str


ChildList = Union[list[str], DynamicChildList]


# =============================================================================
# Component Base
# =============================================================================

class Component(BaseModel):
    """Base component with common properties"""
    id: str
    component: str
    weight: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.model_dump().items() if v is not None}


# =============================================================================
# Display Components
# =============================================================================

class TextComponent(Component):
    """Renders text content with optional markdown"""
    component: str = "Text"
    text: DynamicString
    variant: TextVariant | None = None


class ImageComponent(Component):
    """Displays images"""
    component: str = "Image"
    url: DynamicString
    fit: ImageFit | None = None
    variant: ImageVariant | None = None


class IconComponent(Component):
    """Renders icons from predefined set or custom path"""
    component: str = "Icon"
    name: DynamicString  # Preset name or path


class VideoComponent(Component):
    """Embeds video content"""
    component: str = "Video"
    url: DynamicString


class AudioPlayerComponent(Component):
    """Audio playback component"""
    component: str = "AudioPlayer"
    url: DynamicString
    description: DynamicString | None = None


# =============================================================================
# Layout Components
# =============================================================================

class RowComponent(Component):
    """Horizontal arrangement of children"""
    component: str = "Row"
    children: ChildList
    justify: Justification | None = None
    align: Alignment | None = None


class ColumnComponent(Component):
    """Vertical arrangement of children"""
    component: str = "Column"
    children: ChildList
    justify: Justification | None = None
    align: Alignment | None = None


class ListComponent(Component):
    """Scrollable list of items"""
    component: str = "List"
    children: ChildList
    direction: ListDirection | None = None
    align: Alignment | None = None


class CardComponent(Component):
    """Container with visual styling"""
    component: str = "Card"
    child: str  # Single child component ID


class TabItem(BaseModel):
    """Tab definition"""
    title: DynamicString
    child: str  # Component ID


class TabsComponent(Component):
    """Tabbed interface"""
    component: str = "Tabs"
    tabs: list[TabItem]


class DividerComponent(Component):
    """Visual separator"""
    component: str = "Divider"
    axis: DividerAxis | None = None


class ModalComponent(Component):
    """Overlay dialog"""
    component: str = "Modal"
    trigger: str  # Component ID that opens modal
    content: str  # Component ID shown inside


# =============================================================================
# Input Components
# =============================================================================

class ButtonComponent(Component):
    """Clickable action trigger"""
    component: str = "Button"
    child: str  # Child component ID (typically Text or Icon)
    action: Action
    primary: bool | None = None


class CheckBoxComponent(Component):
    """Boolean toggle"""
    component: str = "CheckBox"
    label: DynamicString
    value: DynamicBoolean
    checks: list[CheckRule] = Field(default_factory=list)


class TextFieldComponent(Component):
    """Text input field"""
    component: str = "TextField"
    label: DynamicString
    value: DynamicString | None = None
    variant: TextFieldVariant | None = None
    checks: list[CheckRule] = Field(default_factory=list)


class ChoiceOption(BaseModel):
    """Option for choice picker"""
    label: DynamicString
    value: DynamicValue


class ChoicePickerComponent(Component):
    """Selection from options"""
    component: str = "ChoicePicker"
    options: list[ChoiceOption]
    value: list[DynamicValue]
    variant: ChoicePickerVariant | None = None
    label: DynamicString | None = None
    checks: list[CheckRule] = Field(default_factory=list)


class SliderComponent(Component):
    """Numeric range input"""
    component: str = "Slider"
    value: DynamicNumber
    min: float | None = None
    max: float | None = None
    label: DynamicString | None = None
    checks: list[CheckRule] = Field(default_factory=list)


class DateTimeInputComponent(Component):
    """Date/time picker"""
    component: str = "DateTimeInput"
    value: DynamicString  # ISO 8601 string
    enableDate: bool | None = None
    enableTime: bool | None = None
    outputFormat: str | None = None
    label: DynamicString | None = None
    checks: list[CheckRule] = Field(default_factory=list)


# =============================================================================
# Server-to-Client Messages
# =============================================================================

class CreateSurfaceMessage(BaseModel):
    """Initialize a new UI surface"""
    createSurface: dict[str, str]  # surfaceId, catalogId

    @classmethod
    def create(cls, surface_id: str, catalog_id: str = "https://a2ui.dev/catalog/standard") -> "CreateSurfaceMessage":
        return cls(createSurface={"surfaceId": surface_id, "catalogId": catalog_id})


class UpdateComponentsMessage(BaseModel):
    """Update the component tree"""
    updateComponents: dict[str, Any]  # surfaceId, components

    @classmethod
    def create(cls, surface_id: str, components: list[dict[str, Any]]) -> "UpdateComponentsMessage":
        return cls(updateComponents={"surfaceId": surface_id, "components": components})


class UpdateDataModelMessage(BaseModel):
    """Update the data model for a surface"""
    updateDataModel: dict[str, Any]  # surfaceId, path (optional), value (optional)

    @classmethod
    def create(cls, surface_id: str, value: Any, path: str = "/") -> "UpdateDataModelMessage":
        return cls(updateDataModel={"surfaceId": surface_id, "path": path, "value": value})


class DeleteSurfaceMessage(BaseModel):
    """Remove a surface"""
    deleteSurface: dict[str, str]  # surfaceId

    @classmethod
    def create(cls, surface_id: str) -> "DeleteSurfaceMessage":
        return cls(deleteSurface={"surfaceId": surface_id})


A2UIServerMessage = Union[
    CreateSurfaceMessage,
    UpdateComponentsMessage,
    UpdateDataModelMessage,
    DeleteSurfaceMessage
]


# =============================================================================
# Client-to-Server Messages
# =============================================================================

class ActionEvent(BaseModel):
    """User-initiated action from UI component"""
    action: dict[str, Any]  # name, surfaceId, sourceComponentId, timestamp, context

    @classmethod
    def create(
        cls,
        name: str,
        surface_id: str,
        source_component_id: str,
        context: dict[str, Any] | None = None,
        timestamp: str | None = None
    ) -> "ActionEvent":
        from datetime import datetime, timezone
        return cls(action={
            "name": name,
            "surfaceId": surface_id,
            "sourceComponentId": source_component_id,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "context": context or {}
        })


class ErrorEvent(BaseModel):
    """Client-side error report"""
    error: dict[str, Any]  # code, surfaceId, message, path (optional)

    @classmethod
    def create(
        cls,
        code: str,
        surface_id: str,
        message: str,
        path: str | None = None
    ) -> "ErrorEvent":
        data = {"code": code, "surfaceId": surface_id, "message": message}
        if path:
            data["path"] = path
        return cls(error=data)


class CapabilitiesEvent(BaseModel):
    """Client UI rendering capabilities"""
    capabilities: dict[str, Any]  # supportedCatalogIds, etc.

    @classmethod
    def create(
        cls,
        supported_catalog_ids: list[str],
        supported_function_catalog_ids: list[str] | None = None
    ) -> "CapabilitiesEvent":
        data: dict[str, Any] = {"supportedCatalogIds": supported_catalog_ids}
        if supported_function_catalog_ids:
            data["supportedFunctionCatalogIds"] = supported_function_catalog_ids
        return cls(capabilities=data)


A2UIClientMessage = Union[ActionEvent, ErrorEvent, CapabilitiesEvent]
