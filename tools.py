import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Type, get_type_hints

from pydantic import BaseModel, create_model

TOOLS_ATTR = "__tools__"

DEFAULT_TOOL_METHODS = ("create", "list", "get", "update", "delete")


@dataclass(frozen=True)
class Tool:
    """
    A service method exposed to an LLM as a tool.

    Parameters typed as pydantic models are flattened into the tool input, so
    the LLM sees e.g. meetings_update(meeting_id, title, ...) rather than a
    nested object; arguments() rebuilds the models from the flat input.
    """

    name: str
    description: str
    service: str
    method: str
    input_model: Type[BaseModel]
    model_params: Tuple[Tuple[str, Type[BaseModel]], ...]

    def definition(self) -> Dict[str, Any]:
        """
        Tool definition in the format expected by the Anthropic Messages API.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
        }

    def arguments(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool input and turn it into keyword arguments for the method.
        """
        validated = self.input_model.model_validate(tool_input)
        provided = validated.model_dump(exclude_unset=True)
        flattened = set()
        kwargs = {}
        for param, model in self.model_params:
            fields = {name: provided[name] for name in model.model_fields if name in provided}
            kwargs[param] = model.model_validate(fields)
            flattened.update(model.model_fields)
        for name in self.input_model.model_fields:
            if name not in flattened:
                kwargs[name] = getattr(validated, name)
        return kwargs


def expose_tools(cls: Optional[type] = None, *, methods: Optional[Iterable[str]] = None):
    """
    Class decorator exposing a service's methods as LLM tools, listed by
    ServiceMesh.get_tools().

    By default exposes the CRUD methods (create, list, get, update, delete)
    that the service defines itself. Tool descriptions come from the methods'
    docstrings, so every exposed method must have one.
    """

    def decorate(service_cls: type) -> type:
        names = methods if methods is not None else [m for m in DEFAULT_TOOL_METHODS if m in vars(service_cls)]
        tools = tuple(_build_tool(service_cls, name) for name in names)
        setattr(service_cls, TOOLS_ATTR, tools)
        return service_cls

    return decorate(cls) if cls is not None else decorate


def collect_tools(service_classes: Iterable[type]) -> Dict[str, Tool]:
    """
    Gather the tools of every @expose_tools service, keyed by tool name.
    """
    return {tool.name: tool for cls in service_classes for tool in getattr(cls, TOOLS_ATTR, ())}


def _build_tool(service_cls: type, method_name: str) -> Tool:
    method: Callable = getattr(service_cls, method_name)
    name = f"{service_cls.name}_{method_name}"
    description = inspect.getdoc(method)
    if not description:
        raise TypeError(f"{service_cls.__name__}.{method_name} needs a docstring to be exposed as a tool")

    hints = get_type_hints(method)
    fields: Dict[str, Any] = {}
    model_params = []
    for param in list(inspect.signature(method).parameters.values())[1:]:
        annotation = hints.get(param.name, Any)
        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            model_params.append((param.name, annotation))
            new_fields = {field_name: (field.annotation, field) for field_name, field in annotation.model_fields.items()}
        else:
            default = ... if param.default is inspect.Parameter.empty else param.default
            new_fields = {param.name: (annotation, default)}
        clashes = fields.keys() & new_fields.keys()
        if clashes:
            raise TypeError(f"{name}: input field(s) {sorted(clashes)} defined more than once")
        fields.update(new_fields)

    input_model = create_model(f"{name}_input", **fields)
    return Tool(name, description, service_cls.name, method_name, input_model, tuple(model_params))
