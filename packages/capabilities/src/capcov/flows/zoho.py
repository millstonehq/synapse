"""Creator export structure and evidence graph, with an explicit source census.

Strings/comments cannot open blocks. Declarations are owned by their container:
web rendering metadata is not a second declaration of a form or report.
The graph contains source facts and labelled candidate dependencies, never
fabricated business outcomes. No source literals or connection values are emitted.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*.*?\*/', re.S)
IDENT = r"[A-Za-z_][A-Za-z_0-9]*"
SCREEN = re.compile(
    r"((?:default )?(?:list|spreadsheet)|form|page|print|pivotchart|pivottable)"
    rf"\s+({IDENT})(?:\(.*\))?$"
)
FUNCTION = re.compile(rf"[\w<>]+\s+({IDENT}(?:\.{IDENT})?)\s*\(")


@dataclass
class Block:
    header: str
    line: int
    start: int
    end: int = 0
    children: list[Block] = field(default_factory=list)


class Export:
    def __init__(self, text: str) -> None:
        self.text = text
        self.mask = TOKEN.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)
        # A leftover quote indicates an unterminated string, not ignorable residue.
        if re.search(r'["\']', self.mask):
            raise ValueError("unterminated string in Creator export")
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.lines = text.splitlines()
        roots: list[Block] = []
        stack: list[Block] = []
        for token in re.finditer(r"[{}]", self.mask):
            line = self.line(token.start()) - 1
            if token.group() == "{":
                header = text[self.starts[line] : token.start()].strip()
                if not header:
                    line -= 1
                    while line >= 0 and not self.lines[line].strip():
                        line -= 1
                    header = self.lines[line].strip() if line >= 0 else ""
                block = Block(header, line + 1, token.start())
                (stack[-1].children if stack else roots).append(block)
                stack.append(block)
            elif not stack:
                raise ValueError(f"unmatched closing brace at line {line + 1}")
            else:
                stack.pop().end = token.end()
        if stack:
            raise ValueError(f"unclosed block at line {stack[-1].line}")
        if len(roots) != 1 or not roots[0].header.startswith("application "):
            raise ValueError("expected one Creator application declaration")
        self.app = roots[0]

    def line(self, position: int) -> int:
        return bisect.bisect_right(self.starts, position)

    def body(self, block: Block, *, literals: bool = False) -> str:
        return (self.text if literals else self.mask)[block.start + 1 : block.end - 1]

    def direct(self, block: Block) -> str:
        """Properties of this owner, excluding nested blocks."""
        body = list(self.body(block, literals=True))
        for child in block.children:
            start = max(0, self.starts[child.line - 1] - block.start - 1)
            end = child.end - block.start - 1
            body[start:end] = ["\n" if c == "\n" else " " for c in body[start:end]]
        return "".join(body)


def children(block: Block, header: str) -> list[Block]:
    return [b for b in block.children if b.header == header]


def descendants(block: Block) -> list[Block]:
    result = []
    for child in block.children:
        result.append(child)
        result.extend(descendants(child))
    return result


def property_value(body: str, name: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.*?)\s*$", body, re.M | re.I)
    return match.group(1).strip().strip('"') if match else None


def derive(text: str, file: str) -> dict:
    export = Export(text)
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    unresolved: list[dict] = []
    census: list[dict] = []
    code: dict[str, Block] = {}
    lookups: dict[tuple[str, str], str] = {}

    def node(name: str, kind: str, block: Block, **extra: object) -> str:
        if name in nodes:
            raise ValueError(f"duplicate Creator declaration: {name}")
        nodes[name] = {
            "id": name,
            "kind": kind,
            "source": {"file": file, "line": block.line},
            **extra,
        }
        return name

    def edge(source: str, target: str, relation: str, line: int, **extra: object) -> None:
        edges.append(
            {
                "from": source,
                "to": target,
                "relation": relation,
                "source": {"file": file, "line": line},
                **extra,
            }
        )

    def gap(owner: str, reason: str, line: int) -> None:
        unresolved.append(
            {"owner": owner, "reason": reason, "source": {"file": file, "line": line}}
        )

    def count(section: str, total: int, classified: int) -> None:
        census.append({"section": section, "declared": total, "classified": classified})

    # Every top-level section receives a policy. Unknown ones cannot disappear.
    top = {b.header: b for b in export.app.children}
    if len(top) != len(export.app.children):
        raise ValueError("duplicate application section")
    supported = {
        "forms",
        "reports",
        "pages",
        "functions",
        "workflow",
        "share_settings",
        "customize",
        "web",
        "phone",
        "tablet",
        "reports configuration",
        "translation",
    }
    for header, block in top.items():
        if header not in supported:
            gap("application", "unsupported top-level section", block.line)
    count("application sections", len(top), len(set(top) & supported))
    for section in ("customize", "reports configuration", "translation"):
        if section in top:
            node(
                f"zoho:configuration:{section}",
                "configuration",
                top[section],
                fixture_dimensions=["locale"] if section == "translation" else ["presentation"],
            )

    for section in ("forms", "reports", "pages"):
        container = top.get(section)
        if container is None:
            gap("application", f"missing {section} section", export.app.line)
            continue
        classified = 0
        for block in container.children:
            match = SCREEN.fullmatch(block.header)
            if not match:
                gap(section, "unrecognised screen declaration", block.line)
                continue
            kind, name = match.groups()
            # print template is a container inside forms, not a global screen.
            identity = node(
                f"zoho:screen:{name}",
                "surface",
                block,
                screen_kind=kind,
                declared_in=section,
                label=property_value(export.direct(block), "displayname") or name,
            )
            classified += 1
            body = export.body(block)
            query = re.search(rf"show all rows from\s+({IDENT})", body)
            entity = query.group(1) if query else name if kind == "form" else None
            nodes[identity]["entity"] = entity
            if kind == "form":
                persists = property_value(export.direct(block), "store data in zc") != "false"
                nodes[identity]["persists"] = persists
                if persists:
                    node(f"zoho:entity:{name}", "entity", block)
                else:
                    entity = None
                    nodes[identity]["entity"] = None
                # Parenthesised field declarations have their own delimiter census.
                pairs: dict[int, int] = {}
                parents: dict[int, int | None] = {}
                stack = []
                for delimiter in re.finditer(r"[()]", body):
                    if delimiter.group() == "(":
                        parents[delimiter.start()] = stack[-1] if stack else None
                        stack.append(delimiter.start())
                    elif stack:
                        pairs[stack.pop()] = delimiter.start()
                    else:
                        gap(identity, "unbalanced field parentheses", block.line)
                if stack:
                    gap(identity, "unclosed field parentheses", block.line)
                field_paths = {}
                metadata_slots = set()
                for match in re.finditer(
                    rf"^[\t ]*(?:must have )?(?:unique )?({IDENT})\s*\n\s*\(", body, re.M
                ):
                    start = match.end() - 1
                    if start not in pairs:
                        continue
                    absolute = block.start + 1 + start
                    if any(child.start < absolute < child.end for child in block.children):
                        continue
                    field_body = body[start + 1 : pairs[start]]
                    if match.group(1) == "customize":
                        metadata_slots.add(start)
                        continue
                    widget = property_value(field_body, "type")
                    if not widget:
                        continue
                    parent_field = field_paths.get(parents[start])
                    field_name = ((parent_field + ".") if parent_field else "") + match.group(1)
                    field_paths[start] = field_name
                    line = export.line(block.start + 1 + match.start())
                    field_id = node(
                        f"zoho:field:{name}:{field_name}",
                        "field",
                        Block("", line, 0),
                        form=name,
                        widget=widget,
                        required="must have " in match.group(),
                        unique="unique " in match.group(),
                    )
                    edge(identity, field_id, "has-field", line)
                    lookup = re.search(rf"\bvalues\s*=\s*({IDENT})(?:\.|\[)", field_body)
                    if lookup:
                        lookups[name, field_name] = lookup.group(1)
                        nodes[field_id]["lookup"] = lookup.group(1)
                        edge(field_id, f"zoho:entity:{lookup.group(1)}", "looks-up", line)
                declared_fields = {
                    start
                    for start in pairs
                    if parents[start] is None
                    and not any(
                        child.start < block.start + 1 + start < child.end
                        for child in block.children
                    )
                }
                count(
                    f"fields {name}",
                    len(declared_fields),
                    len(declared_fields & (set(field_paths) | metadata_slots)),
                )
                for start in sorted(declared_fields - set(field_paths) - metadata_slots):
                    gap(
                        identity,
                        "unsupported field declaration",
                        export.line(block.start + 1 + start),
                    )
            if entity:
                edge(identity, f"zoho:entity:{entity}", "reads" if query else "edits", block.line)
            for match in re.finditer(rf"^\s*workflow\s*=\s*({IDENT})", body, re.M):
                workflow = match.group(1)
                line = export.line(block.start + 1 + match.start())
                action = node(
                    f"{identity}:action:{workflow}:{line}",
                    "action",
                    Block("", line, 0),
                    surface=identity,
                    workflow=workflow,
                )
                edge(identity, action, "offers-action", line)
                edge(action, f"zoho:workflow:functions:{workflow}", "invokes", line)
            if query:
                start = query.end()
                end = body.find("\n", start)
                predicate = body[start : end if end != -1 else len(body)].strip()
                if predicate:
                    guard = node(
                        f"{identity}:filter",
                        "predicate",
                        block,
                        surface=identity,
                        outcomes=["matches", "excluded"],
                        predicate_sha256=hashlib.sha256(predicate.encode()).hexdigest(),
                    )
                    edge(identity, guard, "guarded-by", block.line)
                    for field_name in sorted(set(re.findall(rf"(?:{IDENT}\.)*{IDENT}", predicate))):
                        if "." in field_name and not field_name.startswith("zoho."):
                            nodes[guard].setdefault("field_references", []).append(field_name)
            # Print templates are owned by their form. Equal leaf names remain distinct.
            for template in [b for b in descendants(block) if b.header == "print template"]:
                for view in template.children:
                    if re.fullmatch(IDENT, view.header):
                        view_id = node(
                            f"zoho:screen:{name}::{view.header}",
                            "surface",
                            view,
                            screen_kind="print",
                            entity=name,
                            declared_in="print template",
                        )
                        edge(identity, view_id, "print-view", view.line)
                        edge(view_id, f"zoho:entity:{name}", "reads", view.line)
            if kind == "page":
                # Content is an encoded ZML string; explicit report/form/page references
                # inside it are evidence, not reports-configuration blocks elsewhere.
                raw = export.body(block, literals=True)
                content_match = re.search(r'Content\s*=\s*("(?:\\.|[^"\\])*")', raw, re.S | re.I)
                if content_match:
                    try:
                        content = json.loads(content_match.group(1))
                    except ValueError:
                        gap(identity, "page content could not be decoded", block.line)
                    else:
                        references = set(
                            re.findall(
                                r"(?:#(?:Report|Form|Page):|"
                                r"(?:reportLinkName|formLinkName|pageLinkName|componentLinkName|linkName)\s*=\s*['\"])"
                                r"([A-Za-z_][\w]*)",
                                content,
                                re.I,
                            )
                        )
                        for target in sorted(references):
                            edge(identity, f"zoho:screen:{target}", "page-reference", block.line)
                        gap(
                            identity,
                            "embedded page expressions require runtime confirmation",
                            block.line,
                        )
                else:
                    gap(identity, "page content absent or unsupported", block.line)
        count(section, len(container.children), classified)

    functions = top.get("functions")
    if functions:
        for language in functions.children:
            if language.header != "Deluge":
                gap("functions", "unsupported function language", language.line)
                continue
            classified = 0
            for block in language.children:
                match = FUNCTION.match(block.header)
                if not match:
                    gap("functions", "unrecognised function signature", block.line)
                    continue
                identity = node(f"zoho:function:{match.group(1)}", "function", block)
                code[identity] = block
                classified += 1
            count("Deluge functions", len(language.children), classified)

    workflow = top.get("workflow")
    if workflow:
        for category in workflow.children:
            classified = 0
            for block in category.children:
                match = re.match(rf"({IDENT})\s+as\s+", block.header)
                if not match or category.header not in {"form", "schedule", "functions"}:
                    gap("workflow", "unsupported workflow declaration", block.line)
                    continue
                body = export.direct(block)
                entity = property_value(body, "form")
                identity = node(
                    f"zoho:workflow:{category.header}:{match.group(1)}",
                    "schedule" if category.header == "schedule" else "workflow",
                    block,
                    entity=entity,
                    category=category.header,
                    event=property_value(body, "record event"),
                    button=property_value(body, "button"),
                    active=property_value(body, "status") != "inactive",
                )
                if category.header == "schedule":
                    # Schedule timing is a fixture requirement; no timestamps or literals copied.
                    nodes[identity]["frequency"] = property_value(body, "frequency")
                    nodes[identity]["fixture_dimensions"] = ["clock-before-due", "clock-at-due"]
                    nodes[identity]["outcomes"] = ["not-due", "due"]
                if entity:
                    edge(f"zoho:screen:{entity}", identity, "triggers", block.line)
                nodes[identity]["triggers"] = [
                    b.header
                    for b in block.children
                    if re.fullmatch(r"on [\w .]+|field rules", b.header)
                ]
                code[identity] = block
                classified += 1
            count(f"workflow {category.header}", len(category.children), classified)

    # Resolve function calls, entity accesses and alias-qualified field writes.
    form_fields: dict[str, set[str]] = defaultdict(set)
    for item in nodes.values():
        if item["kind"] == "field":
            form_fields[item["form"]].add(item["id"].split(":")[-1].split(".")[0])
    for identity, block in code.items():
        body = export.body(block)
        locals_ = set(re.findall(rf"(?<![\w.])({IDENT})\s*=(?!=)", body))
        locals_.update(re.findall(IDENT, block.header))
        locals_.update(re.findall(rf"\bfor each\s+({IDENT})", body))
        locals_.update(re.findall(rf"\bcatch\s*\(\s*({IDENT})", body))
        locals_.update({"input", "old", "today", "now", "ID"})
        referenced_entities = set(re.findall(rf"\b({IDENT})\s*\[", body))
        referenced_entities.add(nodes[identity].get("entity"))
        for entity in referenced_entities:
            locals_.update(form_fields.get(entity, set()))
        for call in re.finditer(rf"\b({IDENT}(?:\.{IDENT})+)\s*\(", body):
            callee = call.group(1)
            receiver = callee.split(".")[0]
            if receiver == "thisapp" or receiver in locals_:
                continue
            if callee.startswith(("zoho.currentdate.", "zoho.currenttime.", "zoho.loginuserid.")):
                continue
            line = export.line(block.start + 1 + call.start())
            if f"zoho:entity:{receiver}" in nodes:
                edge(identity, f"zoho:entity:{receiver}", "reads", line)
            elif f"zoho:function:{callee}" in nodes:
                edge(identity, f"zoho:function:{callee}", "calls", line)
            else:
                target = f"zoho:external:{callee}"
                if target not in nodes:
                    node(
                        target,
                        "effect",
                        Block("", line, 0),
                        effect="external-call",
                        callee=callee,
                        outcomes=["success", "failure"],
                    )
                    gap(target, "qualified call dependency has no source in this export", line)
                edge(
                    identity,
                    target,
                    "external-effect",
                    line,
                    confidence="unbound-namespace-candidate",
                )
        aliases: dict[str, set[str]] = {}
        for match in re.finditer(rf"({IDENT})\s*=\s*({IDENT})\s*\[", body):
            aliases.setdefault(match.group(1), set()).add(match.group(2))
        for match in re.finditer(rf"\bfor each\s+({IDENT})\s+in\s+({IDENT})\s*\[", body):
            aliases.setdefault(match.group(1), set()).add(match.group(2))
        for match in re.finditer(rf"\bthisapp\.({IDENT}(?:\.{IDENT})?)\s*\(", body):
            called = match.group(1)
            target = f"zoho:function:{called}"
            if (
                called
                in {
                    "permissions.isUserInProfile",
                    "portal.assignUserInProfile",
                    "portal.deleteUser",
                    "portal.profileForUser",
                }
                and target not in nodes
            ):
                node(target, "platform-operation", block, operation=called)
            edge(
                identity,
                target,
                "calls",
                export.line(block.start + 1 + match.start()),
            )
        for match in re.finditer(rf"\b({IDENT})\s*\[", body):
            entity = match.group(1)
            if f"zoho:entity:{entity}" in nodes:
                edge(
                    identity,
                    f"zoho:entity:{entity}",
                    "reads",
                    export.line(block.start + 1 + match.start()),
                )
        # Assignment targets occur at statement boundaries. A single '=' inside
        # Creator query criteria is a comparison, not a write to that field.
        for match in re.finditer(
            rf"(?:^|[;{{}}])[\t ]*({IDENT})\.({IDENT}(?:\.{IDENT})*)\s*=(?!=)", body, re.M
        ):
            alias, field_name = match.groups()
            targets = aliases.get(alias, set())
            line = export.line(block.start + 1 + match.start())
            current_form = nodes[identity].get("entity")
            input_field = field_name
            if alias == "row":
                triggers = nodes[identity].get("triggers", [])
                trigger = next(
                    (
                        t.removeprefix("on user input of ")
                        for t in triggers
                        if t.startswith("on user input of ") and "." in t
                    ),
                    None,
                )
                if trigger:
                    input_field = trigger.split(".")[0] + "." + field_name
            input_id = f"zoho:field:{current_form}:{input_field}"
            if alias in {"input", "row"} and input_id in nodes:
                edge(identity, input_id, "changes-input", line)
            elif len(targets) == 1:
                entity = next(iter(targets))
                if f"zoho:entity:{entity}" in nodes:
                    edge(
                        identity,
                        f"zoho:entity:{entity}",
                        "writes-field",
                        line,
                        field=field_name,
                        confidence="lexical-alias-candidate",
                    )
            elif alias != "input":
                gap(identity, "unresolved assignment receiver", line)
        for match in re.finditer(rf"\b(insert into|delete from)\s+({IDENT})", body):
            edge(
                identity,
                f"zoho:entity:{match.group(2)}",
                "creates" if match.group(1) == "insert into" else "deletes",
                export.line(block.start + 1 + match.start()),
            )
        for match in re.finditer(r"\b(if|else\s+if|catch)\s*\(", body):
            line = export.line(block.start + 1 + match.start())
            column = block.start + 1 + match.start() - export.starts[line - 1]
            branch = node(
                f"{identity}:branch:{line}:{column}",
                "branch-candidate",
                Block("", line, 0),
                owner=identity,
                outcomes=["handled"] if match.group(1) == "catch" else ["true", "false"],
            )
            edge(identity, branch, "has-branch", line)
        for match in re.finditer(r"\b(invokeurl|sendmail|openUrl)\b", body, re.I):
            line = export.line(block.start + 1 + match.start())
            column = block.start + 1 + match.start() - export.starts[line - 1]
            effect = node(
                f"{identity}:effect:{line}:{column}:{match.group(1).lower()}",
                "effect",
                Block("", line, 0),
                owner=identity,
                effect=match.group(1).lower(),
                outcomes=["success", "failure"],
            )
            edge(identity, effect, "external-effect", line)
        # Navigation target literals may be read, but only validated names are emitted.
        raw = TOKEN.sub(
            lambda m: " " * len(m.group()) if m.group().startswith(("//", "/*")) else m.group(),
            export.body(block, literals=True),
        )
        for match in re.finditer(rf"#(?:Report|Form|Page):({IDENT})", raw):
            edge(
                identity,
                f"zoho:screen:{match.group(1)}",
                "opens",
                export.line(block.start + 1 + match.start()),
                confidence="literal-reference",
            )

    # Preserve both menu axes and device-specific metadata without declaring duplicates.
    for device in ("web", "phone", "tablet"):
        if device not in top:
            continue
        for category in top[device].children:
            if category.header in {"forms", "reports"}:
                for block in category.children:
                    match = re.match(rf"(?:form|report)\s+({IDENT})$", block.header)
                    if match:
                        if f"zoho:screen:{match.group(1)}" not in nodes:
                            gap(
                                device,
                                "rendering metadata references undeclared screen",
                                block.line,
                            )
                    else:
                        gap(device, "unsupported rendering metadata", block.line)
                count(
                    f"{device} {category.header} metadata",
                    len(category.children),
                    sum(
                        bool(re.match(rf"(?:form|report)\s+{IDENT}$", b.header))
                        for b in category.children
                    ),
                )
            elif category.header == "menu":

                def menu(block: Block, ancestors: list[str], device: str = device) -> None:
                    match = re.match(
                        rf"(space|section|form|report|page)\s+({IDENT})$", block.header
                    )
                    if match:
                        kind, name = match.groups()
                        path = [*ancestors, name]
                        identity = node(
                            f"zoho:menu:{device}:{'/'.join(path)}",
                            "navigation",
                            block,
                            path=path,
                            navigation_kind=kind,
                        )
                        if kind in {"form", "report", "page"}:
                            edge(identity, f"zoho:screen:{name}", "navigates-to", block.line)
                        if ancestors:
                            edge(
                                f"zoho:menu:{device}:{'/'.join(ancestors)}",
                                identity,
                                "contains",
                                block.line,
                            )
                        for child in block.children:
                            menu(child, path)
                    elif block.header == "unused":
                        node(
                            f"zoho:menu:{device}:unused",
                            "navigation",
                            block,
                            navigation_kind="unused",
                            path=["unused"],
                        )
                        for child in block.children:
                            menu(child, ["unused"])
                    elif block.header == "systemcomponent":
                        component = property_value(export.direct(block), "type")
                        component_id = node(
                            f"zoho:menu:{device}:system:{block.line}",
                            "platform-operation",
                            block,
                            operation=component,
                        )
                        if ancestors:
                            edge(
                                f"zoho:menu:{device}:{'/'.join(ancestors)}",
                                component_id,
                                "contains",
                                block.line,
                            )
                    elif block.header == "preference":
                        count(f"{device} menu preferences", 1, 1)
                    else:
                        gap(device, "unsupported navigation declaration", block.line)

                for block in category.children:
                    menu(block, [])
            elif category.header != "customize":
                gap(device, "unsupported device section", category.line)

    profiles = top.get("share_settings")
    if profiles:
        for block in profiles.children:
            if block.header == "roles":
                for role in descendants(block):
                    if re.fullmatch(r'"[\w -]+"', role.header):
                        node(f"zoho:role:{role.header[1:-1]}", "role", role)
                continue
            if not re.fullmatch(r'"[\w -]+"', block.header):
                gap("share_settings", "unsupported permission profile", block.line)
                continue
            profile = block.header[1:-1]
            identity = node(f"zoho:profile:{profile}", "profile", block)
            for modules in children(block, "ModulePermissions"):
                for module in modules.children:
                    if not re.fullmatch(IDENT, module.header):
                        gap(identity, "unsupported module permission", module.line)
                        continue
                    permissions = property_value(export.direct(module), "enabled")
                    for operation in (permissions or "").split(","):
                        operation = operation.strip()
                        if operation:
                            grant = node(
                                f"{identity}:grant:{module.header}:{operation}",
                                "grant",
                                module,
                                actor=profile,
                                outcomes=["allowed", "denied"],
                                operation=operation,
                                surface=f"zoho:screen:{module.header}",
                            )
                            edge(identity, grant, "grants", module.line)
                            edge(grant, f"zoho:screen:{module.header}", "allows", module.line)
            # ReportPermissions use inline sets; parse only closed operation names.
            for permissions in [b for b in descendants(block) if b.header == "ReportPermissions"]:
                for match in re.finditer(
                    rf"({IDENT})\s*=\s*\{{([^}}]*)\}}", export.body(permissions, literals=True)
                ):
                    screen, operations = match.groups()
                    for operation in re.findall(r'"([A-Za-z]+)"', operations):
                        name = f"{identity}:report-grant:{screen}:{operation}"
                        if name not in nodes:
                            grant = node(
                                name,
                                "grant",
                                permissions,
                                actor=profile,
                                outcomes=["allowed", "denied"],
                                operation=operation,
                                surface=f"zoho:screen:{screen}",
                            )
                            edge(identity, grant, "grants", permissions.line)
                            edge(grant, f"zoho:screen:{screen}", "allows", permissions.line)

    # Resolve joins in report filters. A writer to Stores.Login_List can now be
    # related to a pricing report reading Store.Login_List through its lookup.
    for predicate in [n for n in nodes.values() if n["kind"] == "predicate"]:
        owner_entity = nodes[predicate["surface"]].get("entity")
        for reference in predicate.get("field_references", []):
            entity = owner_entity
            for part in reference.split("."):
                field_id = f"zoho:field:{entity}:{part}"
                if field_id not in nodes:
                    break
                edge(predicate["id"], field_id, "reads-field", predicate["source"]["line"])
                entity = lookups.get((entity, part))
                if entity is None:
                    break
    for item in list(edges):
        if item["relation"] == "writes-field":
            entity = item["to"].removeprefix("zoho:entity:")
            field_id = f"zoho:field:{entity}:{item['field']}"
            if field_id in nodes:
                edge(
                    item["from"],
                    field_id,
                    "writes-state",
                    item["source"]["line"],
                    confidence="lexical-alias-candidate",
                )

    # No missing target is silently dropped. Duplicate references remain one evidence edge.
    edges = list({json.dumps(e, sort_keys=True): e for e in edges}.values())
    for item in edges:
        for end in ("from", "to"):
            if item[end] not in nodes:
                gap(item[end], f"unresolved {item['relation']} {end}", item["source"]["line"])
    unresolved = list({json.dumps(g, sort_keys=True): g for g in unresolved}.values())
    return {
        "version": 1,
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "edges": sorted(
            edges, key=lambda e: (e["from"], e["relation"], e["to"], e["source"]["line"])
        ),
        "unresolved": sorted(
            unresolved, key=lambda g: (g["owner"], g["source"]["line"], g["reason"])
        ),
        "census": census,
        "summary": dict(sorted(Counter(n["kind"] for n in nodes.values()).items())),
        "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
