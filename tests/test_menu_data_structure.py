"""
Alap struktúra tesztek a menu_data.py menüfához.

Cél:
- legyen legalább egy főmenü elem
- minden elem rendelkezzen label mezővel
- minden elem rendelkezzen kind mezővel
"""


def walk_menu(items):
    """Rekurzívan bejárja a teljes menüfát."""
    for item in items:
        yield item

        if item.get("kind") == "menu":
            yield from walk_menu(item["children"])


def test_root_menu_not_empty(menu_root):
    """A főmenü nem lehet üres."""
    assert len(menu_root) > 0


def test_every_item_has_label(menu_root):
    """Minden menüelem rendelkezzen nem üres label mezővel."""
    for item in walk_menu(menu_root):
        assert "label" in item
        assert item["label"].strip() != ""


def test_every_item_has_kind(menu_root):
    """Minden menüelem rendelkezzen érvényes kind mezővel."""
    for item in walk_menu(menu_root):
        assert "kind" in item
        assert item["kind"] in ("menu", "leaf")
