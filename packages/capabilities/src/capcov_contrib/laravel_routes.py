"""Laravel route reader, brought in through the plugin seam.

A tree-sitter query sees one call at a time. Laravel's route surface is the
COMPOSITION of nested `Route::group(['prefix' => ...], fn)` and fluent
`Route::prefix(...)->group(fn)` scopes around each `Route::get(...)`, so a query
that captures the literal reads '/' for every index route in the codebase and
the inventory collapses. This reader walks the syntax tree with a prefix stack
and emits the path the router serves.

What it refuses to do, in the package's usual style:

* a non-literal path (`Route::get($x, ...)`) is a `dynamic-route` unresolved entry;
* a non-literal prefix (`['prefix' => $tenant]`) makes every route beneath it a
  `dynamic-prefix` unresolved entry -- the subtree is named, not emitted with a
  guessed path;
* a second declaration of the same METHOD+path is reported under
  `excluded_surfaces` with reason "duplicate ..." -- visible, not a silent dedupe;
* no route file at all is a `no-surfaces` unresolved entry, never an empty green.

Handler styles read: `[Controller::class, 'method']`, `'Controller@method'`,
`['uses' => 'Controller@method']`, closures ("closure"). `resource` /
`apiResource` expand to Laravel's canonical action set, honouring `->only([...])`
and `->except([...])`. `match([...], path, h)` emits one surface per verb;
`any(path, h)` emits the five recognised verbs.

Plugin contract (CORE path, see capcov/PLUGINS.md):
    discover(source_root, target, config) -> core dict
"""

from __future__ import annotations

from pathlib import Path

from capcov.adapters import build_core_dict

NAME = "laravel-routes"
LANGUAGE = "php"
DEFAULT_GLOBS = ["routes/**/*.php", "app/**/Routes/**/*.php"]
VERBS = ("get", "post", "put", "patch", "delete")
ROUTE_FACADES = {"Route", "\\Route", "Illuminate\\Support\\Facades\\Route"}

# Node-type names the installed tree-sitter PHP grammar uses; the ONE place to
# adjust if a grammar upgrade renames them.
CLOSURE_TYPES = ("anonymous_function", "anonymous_function_creation_expression", "arrow_function")
STRING_TYPES = ("string", "encapsed_string")
ARRAY_TYPE = "array_creation_expression"
ARRAY_ELEMENT_TYPE = "array_element_initializer"
CLASS_CONSTANT_TYPE = "class_constant_access_expression"

# Laravel's resource controller actions: name -> (verb, path suffix).
RESOURCE_ACTIONS = [
    ("index", "GET", ""),
    ("create", "GET", "/create"),
    ("store", "POST", ""),
    ("show", "GET", "/{param}"),
    ("edit", "GET", "/{param}/edit"),
    ("update", "PUT", "/{param}"),
    ("update", "PATCH", "/{param}"),
    ("destroy", "DELETE", "/{param}"),
]
API_RESOURCE_OMITS = {"create", "edit"}


def _join(prefix: str, path: str) -> str:
    parts = [p for p in (prefix.strip("/") + "/" + path.strip("/")).split("/") if p]
    return "/" + "/".join(parts)


def _singular(name: str) -> str:
    # Laravel's resource parameter is Str::singular of the last URI segment; the
    # common English cases suffice here, the rest fall through unchanged.
    last = name.strip("/").split("/")[-1]
    if last.endswith("ies"):
        return last[:-3] + "y"
    if last.endswith("ses") or last.endswith("xes"):
        return last[:-2]
    if last.endswith("s") and not last.endswith("ss"):
        return last[:-1]
    return last


class _Reader:
    def __init__(self, relative: str, source: bytes) -> None:
        self.relative = relative
        self.source = source
        self.records: list[dict] = []
        self.excluded: list[dict] = []
        self.unresolved: list[dict] = []
        self.seen: dict[str, tuple[str, int]] = {}

    # -- tree helpers -------------------------------------------------------
    def text(self, node) -> str:
        return self.source[node.start_byte:node.end_byte].decode("utf-8", "replace")

    def line(self, node) -> int:
        return node.start_point[0] + 1

    @staticmethod
    def children(node, *types: str):
        return [c for c in node.named_children if c.type in types]

    def string_literal(self, node) -> str | None:
        """The content of a single- or double-quoted literal, else None."""
        if node.type in STRING_TYPES:
            inner = [c for c in node.named_children if c.type == "string_content"]
            if node.type == "encapsed_string" and any(
                c.type != "string_content" for c in node.named_children
            ):
                return None  # interpolation: not a literal
            return self.text(inner[0]) if inner else ""
        return None

    def call_parts(self, node):
        """(facade_or_None, method_name, arguments_node) for a scoped call."""
        if node.type != "scoped_call_expression":
            return None
        scope = node.child_by_field_name("scope")
        name = node.child_by_field_name("name")
        args = node.child_by_field_name("arguments")
        if scope is None or name is None or args is None:
            return None
        return self.text(scope).lstrip("\\"), self.text(name), args

    def arguments(self, args_node) -> list:
        return [a.named_children[0] for a in args_node.named_children
                if a.type == "argument" and a.named_children]

    # -- handlers -----------------------------------------------------------
    def handler(self, node) -> str:
        if node is None:
            return "closure"
        if node.type in CLOSURE_TYPES:
            return "closure"
        literal = self.string_literal(node)
        if literal is not None:
            return literal
        if node.type == ARRAY_TYPE:
            elements = self.children(node, ARRAY_ELEMENT_TYPE)
            # ['uses' => 'C@m']
            for element in elements:
                kids = element.named_children
                if len(kids) == 2 and self.string_literal(kids[0]) == "uses":
                    value = self.string_literal(kids[1])
                    if value is not None:
                        return value
            # [C::class, 'm']
            if len(elements) == 2:
                first, second = elements[0].named_children[-1], elements[1].named_children[-1]
                method = self.string_literal(second)
                if first.type == CLASS_CONSTANT_TYPE and method is not None:
                    cls = self.text(first).rsplit("::", 1)[0].lstrip("\\").split("\\")[-1]
                    return f"{cls}@{method}"
        return self.text(node)[:80]

    # -- emission -----------------------------------------------------------
    def emit(self, verb: str, path: str, handler: str, node) -> None:
        sid = f"http:{verb} {path}"
        line = self.line(node)
        if sid in self.seen:
            first_file, first_line = self.seen[sid]
            self.excluded.append({
                "file": self.relative, "line": line, "method": verb, "path": path,
                "handler": handler,
                "reason": f"duplicate declaration of {sid}; first at {first_file}:{first_line}",
            })
            return
        self.seen[sid] = (self.relative, line)
        self.records.append({
            "id": sid, "method": verb, "path": path, "handler": handler,
            "file": self.relative, "line": line, "module": self.relative,
        })

    def unresolved_entry(self, kind: str, reason: str, node) -> None:
        self.unresolved.append({
            "adapter": NAME, "kind": kind, "reason": reason,
            "file": self.relative, "line": self.line(node),
        })

    # -- walking ------------------------------------------------------------
    def walk(self, node, prefix: str, dynamic: bool) -> None:
        handled = self.route_call(node, prefix, dynamic)
        if handled:
            return
        for child in node.children:
            self.walk(child, prefix, dynamic)

    def group_scope(self, node):
        """If `node` is a group call, return (prefix_literal_or_None, is_dynamic, body)."""
        # Route::group([...], function () {...})
        parts = self.call_parts(node)
        if parts and parts[0] in ROUTE_FACADES and parts[1] == "group":
            args = self.arguments(parts[2])
            if len(args) >= 2:
                return self.prefix_from_array(args[0]) + (args[1],)
            if len(args) == 1:
                return None, False, args[0]
        # Route::prefix('x')->middleware(...)->group(function () {...})
        if node.type == "member_call_expression":
            name = node.child_by_field_name("name")
            args_node = node.child_by_field_name("arguments")
            if name is not None and self.text(name) == "group" and args_node is not None:
                body_args = self.arguments(args_node)
                prefix, dynamic = self.prefix_from_chain(node.child_by_field_name("object"))
                if prefix is not None or dynamic:
                    return prefix, dynamic, (body_args[0] if body_args else None)
                if self.chain_root_is_route(node.child_by_field_name("object")):
                    return None, False, (body_args[0] if body_args else None)
        return None

    def chain_root_is_route(self, node) -> bool:
        while node is not None and node.type == "member_call_expression":
            node = node.child_by_field_name("object")
        parts = self.call_parts(node) if node is not None else None
        return bool(parts and parts[0] in ROUTE_FACADES)

    def prefix_from_chain(self, node):
        """Walk a fluent chain collecting prefix(...) calls down to the facade."""
        prefixes: list[str] = []
        dynamic = False
        while node is not None:
            if node.type == "member_call_expression":
                name = node.child_by_field_name("name")
                args_node = node.child_by_field_name("arguments")
                if name is not None and self.text(name) == "prefix" and args_node is not None:
                    args = self.arguments(args_node)
                    literal = self.string_literal(args[0]) if args else None
                    if literal is None:
                        dynamic = True
                    else:
                        prefixes.append(literal)
                node = node.child_by_field_name("object")
                continue
            parts = self.call_parts(node)
            if parts and parts[0] in ROUTE_FACADES:
                if parts[1] == "prefix":
                    args = self.arguments(parts[2])
                    literal = self.string_literal(args[0]) if args else None
                    if literal is None:
                        dynamic = True
                    else:
                        prefixes.append(literal)
                break
            return None, False
        if not prefixes and not dynamic:
            return None, False
        # innermost call is outermost in the chain text; compose in source order
        return "/".join(p.strip("/") for p in reversed(prefixes)), dynamic

    def prefix_from_array(self, node):
        if node.type != ARRAY_TYPE:
            return None, False
        for element in self.children(node, ARRAY_ELEMENT_TYPE):
            kids = element.named_children
            if len(kids) == 2 and self.string_literal(kids[0]) == "prefix":
                literal = self.string_literal(kids[1])
                return (literal, False) if literal is not None else (None, True)
        return None, False

    def route_call(self, node, prefix: str, dynamic: bool) -> bool:
        scope = self.group_scope(node)
        if scope is not None:
            group_prefix, group_dynamic, body = scope
            if group_dynamic:
                self.unresolved_entry(
                    "dynamic-prefix",
                    "Route group prefix is not a literal; routes beneath it are not emitted",
                    node,
                )
            new_prefix = _join(prefix, group_prefix) if group_prefix else prefix
            if body is not None:
                self.walk(body, new_prefix, dynamic or group_dynamic)
            return True
        parts = self.call_parts(node)
        if not parts or parts[0] not in ROUTE_FACADES:
            return False
        facade, method, args_node = parts
        args = self.arguments(args_node)
        if method in VERBS or method in ("any", "match"):
            if method == "match":
                if len(args) < 2 or args[0].type != ARRAY_TYPE:
                    self.unresolved_entry("dynamic-route", "Route::match verbs are not a literal array", node)
                    return True
                verbs = [v.upper() for v in (self.string_literal(e.named_children[-1]) or ""
                         for e in self.children(args[0], ARRAY_ELEMENT_TYPE)) if v]
                path_node, handler_node = args[1], (args[2] if len(args) > 2 else None)
            else:
                verbs = [v.upper() for v in VERBS] if method == "any" else [method.upper()]
                path_node, handler_node = (args[0] if args else None), (args[1] if len(args) > 1 else None)
            literal = self.string_literal(path_node) if path_node is not None else None
            if literal is None:
                self.unresolved_entry("dynamic-route", "route path is not a string literal", node)
                return True
            if dynamic:
                self.unresolved_entry("dynamic-prefix", f"route {literal!r} sits under a non-literal prefix", node)
                return True
            path = _join(prefix, literal)
            handler = self.handler(handler_node)
            for verb in verbs:
                self.emit(verb, path, handler, node)
            return True
        if method in ("resource", "apiResource"):
            literal = self.string_literal(args[0]) if args else None
            if literal is None:
                self.unresolved_entry("dynamic-route", f"Route::{method} name is not a literal", node)
                return True
            if dynamic:
                self.unresolved_entry("dynamic-prefix", f"resource {literal!r} sits under a non-literal prefix", node)
                return True
            controller = self.handler(args[1]) if len(args) > 1 else "closure"
            if "@" not in controller and controller != "closure":
                controller = controller.lstrip("\\").split("\\")[-1].replace("::class", "")
            only, except_ = self.resource_filters(node)
            base = _join(prefix, literal)
            param = _singular(literal)
            for action, verb, suffix in RESOURCE_ACTIONS:
                if method == "apiResource" and action in API_RESOURCE_OMITS:
                    continue
                if only is not None and action not in only:
                    continue
                if except_ is not None and action in except_:
                    continue
                self.emit(verb, base + suffix.replace("{param}", "{" + param + "}"),
                          f"{controller}@{action}", node)
            return True
        return False

    def resource_filters(self, node):
        """->only([...]) / ->except([...]) chained onto a resource call."""
        only = except_ = None
        parent = node.parent
        while parent is not None and parent.type == "member_call_expression":
            name = parent.child_by_field_name("name")
            args_node = parent.child_by_field_name("arguments")
            if name is not None and args_node is not None:
                args = self.arguments(args_node)
                if args and args[0].type == ARRAY_TYPE:
                    names = {self.string_literal(e.named_children[-1])
                             for e in self.children(args[0], ARRAY_ELEMENT_TYPE)}
                    if self.text(name) == "only":
                        only = names
                    elif self.text(name) == "except":
                        except_ = names
            parent = parent.parent
        return only, except_


def discover(source_root, target, config: dict | None = None) -> dict:
    """The CORE-path plugin entry point (see capcov/PLUGINS.md)."""
    try:
        import tree_sitter as ts
        from tree_sitter_language_pack import get_language
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise SystemExit(
            "laravel-routes needs the treesitter extra: pip install 'synapse-capabilities[treesitter]'"
        ) from exc
    root = Path(source_root)
    globs = list((config or {}).get("globs") or DEFAULT_GLOBS)
    parser = ts.Parser(get_language(LANGUAGE))
    records: list[dict] = []
    excluded: list[dict] = []
    unresolved: list[dict] = []
    seen: dict[str, tuple[str, int]] = {}
    files = sorted({p for g in globs for p in root.glob(g) if p.is_file()})
    for path in files:
        source = path.read_bytes()
        reader = _Reader(str(path.relative_to(root)), source)
        reader.seen = seen  # duplicates are global across route files
        tree = parser.parse(source)
        reader.walk(tree.root_node, "", False)
        records.extend(reader.records)
        excluded.extend(reader.excluded)
        unresolved.extend(reader.unresolved)
    if not records:
        unresolved.append({
            "adapter": NAME, "kind": "no-surfaces",
            "reason": f"no Laravel route declarations found under {globs}",
        })
    return build_core_dict(
        records,
        {"count": len(excluded), "surfaces": excluded},
        unresolved,
    )
