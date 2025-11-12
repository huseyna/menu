from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from django import template
from django.http import HttpRequest

from tree_menu.models import MenuItem

register = template.Library()


@dataclass
class MenuNode:
    item: MenuItem
    url: str
    children: List["MenuNode"] = field(default_factory=list)
    parent: Optional["MenuNode"] = None
    is_active: bool = False
    is_open: bool = False


def _normalize_path(path: str) -> str:
    path = path.strip().lstrip("/")
    return f"/{path.rstrip('/')}" if path else "/"


def _normalize_href(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return f"/{url.lstrip('/')}"


def _build_tree(items: Iterable[MenuItem], current_path: str) -> List[MenuNode]:
    nodes: Dict[int, MenuNode] = {}
    roots: List[MenuNode] = []
    active_node: Optional[MenuNode] = None

    for item in items:
        node_url = _normalize_href(item.get_url() or "")
        nodes[item.id] = MenuNode(item=item, url=node_url)

    for item in items:
        node = nodes[item.id]
        if item.parent_id:
            parent = nodes.get(item.parent_id)
            if parent:
                node.parent = parent
                parent.children.append(node)
        else:
            roots.append(node)

        if _normalize_path(node.url) == current_path:
            active_node = node

    expanded_nodes = set()
    if active_node:
        active_node.is_active = True
        expanded_nodes.add(active_node.item.id)
        parent = active_node.parent
        while parent:
            parent.is_open = True
            expanded_nodes.add(parent.item.id)
            parent = parent.parent

    for node in nodes.values():
        node.is_open |= node.item.id in expanded_nodes

    return roots


@register.inclusion_tag("tree_menu/menu.html", takes_context=True)
def draw_menu(context: dict, menu_name: str) -> dict:
    request: Optional[HttpRequest] = context.get("request")
    if not request:
        raise RuntimeError("The 'request' context variable is required for the draw_menu tag.")

    current_path = _normalize_path(request.path)

    items = list(
        MenuItem.objects.filter(menu__name=menu_name)
        .select_related("parent", "menu")
        .order_by("parent__id", "order", "id")
    )

    if not items:
        raise ValueError(f"No items found for menu '{menu_name}'")

    tree = _build_tree(items, current_path)

    return {
        "menu_name": menu_name,
        "menu_tree": tree,
        "current_path": current_path,
    }
