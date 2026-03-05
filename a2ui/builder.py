"""
A2UI Builder - Fluent API for constructing A2UI messages and components

Provides a convenient builder pattern for creating A2UI surfaces and components.
"""

from typing import Any
from .protocol import (
    CreateSurfaceMessage,
    UpdateComponentsMessage,
    UpdateDataModelMessage,
    DeleteSurfaceMessage,
    A2UIServerMessage,
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
    TabItem,
    ChoiceOption,
    Action,
    ActionContext,
    CheckRule,
    PathBinding,
    DynamicChildList,
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


class ComponentBuilder:
    """Builder for creating A2UI components with fluent API"""

    @staticmethod
    def path(data_path: str) -> PathBinding:
        """Create a path binding to data model"""
        return PathBinding(path=data_path)

    @staticmethod
    def text(
        id: str,
        text: str | PathBinding,
        variant: TextVariant | None = None,
        weight: float | None = None
    ) -> TextComponent:
        """Create a Text component"""
        return TextComponent(id=id, text=text, variant=variant, weight=weight)

    @staticmethod
    def image(
        id: str,
        url: str | PathBinding,
        fit: ImageFit | None = None,
        variant: ImageVariant | None = None,
        weight: float | None = None
    ) -> ImageComponent:
        """Create an Image component"""
        return ImageComponent(id=id, url=url, fit=fit, variant=variant, weight=weight)

    @staticmethod
    def icon(id: str, name: str | PathBinding, weight: float | None = None) -> IconComponent:
        """Create an Icon component"""
        return IconComponent(id=id, name=name, weight=weight)

    @staticmethod
    def button(
        id: str,
        child: str,
        action_name: str,
        context: list[tuple[str, Any]] | None = None,
        primary: bool | None = None,
        weight: float | None = None
    ) -> ButtonComponent:
        """Create a Button component"""
        action_context = [ActionContext(key=k, value=v) for k, v in (context or [])]
        action = Action(name=action_name, context=action_context)
        return ButtonComponent(id=id, child=child, action=action, primary=primary, weight=weight)

    @staticmethod
    def text_field(
        id: str,
        label: str | PathBinding,
        value: str | PathBinding | None = None,
        variant: TextFieldVariant | None = None,
        checks: list[CheckRule] | None = None,
        weight: float | None = None
    ) -> TextFieldComponent:
        """Create a TextField component"""
        return TextFieldComponent(
            id=id, label=label, value=value, variant=variant,
            checks=checks or [], weight=weight
        )

    @staticmethod
    def checkbox(
        id: str,
        label: str | PathBinding,
        value: bool | PathBinding,
        checks: list[CheckRule] | None = None,
        weight: float | None = None
    ) -> CheckBoxComponent:
        """Create a CheckBox component"""
        return CheckBoxComponent(id=id, label=label, value=value, checks=checks or [], weight=weight)

    @staticmethod
    def choice_picker(
        id: str,
        options: list[tuple[str, Any]],
        value: list[Any],
        variant: ChoicePickerVariant | None = None,
        label: str | PathBinding | None = None,
        weight: float | None = None
    ) -> ChoicePickerComponent:
        """Create a ChoicePicker component"""
        choice_options = [ChoiceOption(label=lbl, value=val) for lbl, val in options]
        return ChoicePickerComponent(
            id=id, options=choice_options, value=value,
            variant=variant, label=label, weight=weight
        )

    @staticmethod
    def slider(
        id: str,
        value: float | PathBinding,
        min_val: float | None = None,
        max_val: float | None = None,
        label: str | PathBinding | None = None,
        weight: float | None = None
    ) -> SliderComponent:
        """Create a Slider component"""
        return SliderComponent(id=id, value=value, min=min_val, max=max_val, label=label, weight=weight)

    @staticmethod
    def datetime_input(
        id: str,
        value: str | PathBinding,
        enable_date: bool | None = None,
        enable_time: bool | None = None,
        label: str | PathBinding | None = None,
        weight: float | None = None
    ) -> DateTimeInputComponent:
        """Create a DateTimeInput component"""
        return DateTimeInputComponent(
            id=id, value=value, enableDate=enable_date,
            enableTime=enable_time, label=label, weight=weight
        )

    @staticmethod
    def row(
        id: str,
        children: list[str] | DynamicChildList,
        justify: Justification | None = None,
        align: Alignment | None = None,
        weight: float | None = None
    ) -> RowComponent:
        """Create a Row component"""
        return RowComponent(id=id, children=children, justify=justify, align=align, weight=weight)

    @staticmethod
    def column(
        id: str,
        children: list[str] | DynamicChildList,
        justify: Justification | None = None,
        align: Alignment | None = None,
        weight: float | None = None
    ) -> ColumnComponent:
        """Create a Column component"""
        return ColumnComponent(id=id, children=children, justify=justify, align=align, weight=weight)

    @staticmethod
    def list_view(
        id: str,
        children: list[str] | DynamicChildList,
        direction: ListDirection | None = None,
        align: Alignment | None = None,
        weight: float | None = None
    ) -> ListComponent:
        """Create a List component"""
        return ListComponent(id=id, children=children, direction=direction, align=align, weight=weight)

    @staticmethod
    def card(id: str, child: str, weight: float | None = None) -> CardComponent:
        """Create a Card component"""
        return CardComponent(id=id, child=child, weight=weight)

    @staticmethod
    def tabs(id: str, tabs: list[tuple[str, str]], weight: float | None = None) -> TabsComponent:
        """Create a Tabs component"""
        tab_items = [TabItem(title=title, child=child) for title, child in tabs]
        return TabsComponent(id=id, tabs=tab_items, weight=weight)

    @staticmethod
    def divider(id: str, axis: DividerAxis | None = None, weight: float | None = None) -> DividerComponent:
        """Create a Divider component"""
        return DividerComponent(id=id, axis=axis, weight=weight)

    @staticmethod
    def modal(id: str, trigger: str, content: str, weight: float | None = None) -> ModalComponent:
        """Create a Modal component"""
        return ModalComponent(id=id, trigger=trigger, content=content, weight=weight)

    @staticmethod
    def dynamic_children(component_id: str, path: str) -> DynamicChildList:
        """Create dynamic children from data model"""
        return DynamicChildList(componentId=component_id, path=path)

    @staticmethod
    def check_rule(call: str, message: str = "", **args: Any) -> CheckRule:
        """Create a validation check rule"""
        return CheckRule(call=call, message=message, args=args)


class SurfaceBuilder:
    """Builder for constructing a complete A2UI surface"""

    def __init__(self, surface_id: str, catalog_id: str = "https://a2ui.dev/catalog/standard"):
        self.surface_id = surface_id
        self.catalog_id = catalog_id
        self._components: list[Component] = []
        self._data_model: dict[str, Any] = {}
        self._data_updates: list[tuple[str, Any]] = []

    def add_component(self, component: Component) -> "SurfaceBuilder":
        """Add a component to the surface"""
        self._components.append(component)
        return self

    def add_components(self, *components: Component) -> "SurfaceBuilder":
        """Add multiple components to the surface"""
        self._components.extend(components)
        return self

    def set_data(self, path: str, value: Any) -> "SurfaceBuilder":
        """Set a value in the data model"""
        self._data_updates.append((path, value))
        return self

    def set_root_data(self, data: dict[str, Any]) -> "SurfaceBuilder":
        """Set the entire root data model"""
        self._data_model = data
        return self

    def build_messages(self) -> list[A2UIServerMessage]:
        """Build all messages needed to create and populate the surface"""
        messages: list[A2UIServerMessage] = []

        # Create surface
        messages.append(CreateSurfaceMessage.create(self.surface_id, self.catalog_id))

        # Update components
        if self._components:
            components_data = [self._component_to_dict(c) for c in self._components]
            messages.append(UpdateComponentsMessage.create(self.surface_id, components_data))

        # Update data model
        if self._data_model:
            messages.append(UpdateDataModelMessage.create(self.surface_id, self._data_model, "/"))

        for path, value in self._data_updates:
            messages.append(UpdateDataModelMessage.create(self.surface_id, value, path))

        return messages

    def _component_to_dict(self, component: Component) -> dict[str, Any]:
        """Convert component to dictionary format"""
        data = component.model_dump(exclude_none=True)
        # Handle PathBinding objects
        return self._convert_bindings(data)

    def _convert_bindings(self, obj: Any) -> Any:
        """Recursively convert PathBinding objects to dict format"""
        if isinstance(obj, PathBinding):
            return {"path": obj.path}
        elif isinstance(obj, dict):
            return {k: self._convert_bindings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_bindings(item) for item in obj]
        return obj

    def to_json(self) -> list[dict[str, Any]]:
        """Convert all messages to JSON-serializable format"""
        return [msg.model_dump() for msg in self.build_messages()]


class A2UIBuilder:
    """Main builder class for A2UI protocol"""

    def __init__(self):
        self._surfaces: dict[str, SurfaceBuilder] = {}

    def create_surface(
        self,
        surface_id: str,
        catalog_id: str = "https://a2ui.dev/catalog/standard"
    ) -> SurfaceBuilder:
        """Create a new surface builder"""
        builder = SurfaceBuilder(surface_id, catalog_id)
        self._surfaces[surface_id] = builder
        return builder

    def get_surface(self, surface_id: str) -> SurfaceBuilder | None:
        """Get an existing surface builder"""
        return self._surfaces.get(surface_id)

    def delete_surface(self, surface_id: str) -> DeleteSurfaceMessage:
        """Create a delete surface message"""
        if surface_id in self._surfaces:
            del self._surfaces[surface_id]
        return DeleteSurfaceMessage.create(surface_id)

    def build_all_messages(self) -> list[A2UIServerMessage]:
        """Build all messages for all surfaces"""
        messages: list[A2UIServerMessage] = []
        for builder in self._surfaces.values():
            messages.extend(builder.build_messages())
        return messages

    @staticmethod
    def component() -> type[ComponentBuilder]:
        """Access component builder methods"""
        return ComponentBuilder
