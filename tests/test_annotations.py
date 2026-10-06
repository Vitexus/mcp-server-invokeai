import asyncio
import importlib
import sys

import pytest


def _tools(monkeypatch, read_only=False):
    if read_only:
        monkeypatch.setenv("INVOKEAI_READ_ONLY", "true")
    else:
        monkeypatch.delenv("INVOKEAI_READ_ONLY", raising=False)
    sys.modules.pop("invokeai_mcp_server", None)
    mod = importlib.import_module("invokeai_mcp_server")
    return asyncio.run(mod.mcp.list_tools())


def test_every_tool_has_title_and_annotations(monkeypatch):
    tools = _tools(monkeypatch)
    assert {t.name for t in tools} == {
        "generate_image", "img2img", "upscale_image", "list_models", "get_queue_status",
    }
    for t in tools:
        assert t.title and t.title != t.name
        a = t.annotations
        assert a is not None
        for hint in ("read_only_hint", "destructive_hint", "idempotent_hint", "open_world_hint"):
            assert getattr(a, hint) is not None
        assert not (a.read_only_hint and a.destructive_hint)
        if t.name.startswith(("get_", "list_")):
            assert a.read_only_hint is True


def test_read_only_mode_registers_only_read_tools(monkeypatch):
    tools = _tools(monkeypatch, read_only=True)
    assert {t.name for t in tools} == {"list_models", "get_queue_status"}
    assert all(t.annotations.read_only_hint for t in tools)
