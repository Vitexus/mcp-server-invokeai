#!/usr/bin/python3
"""Launcher for the InvokeAI MCP server (stdio transport)."""
import sys
from importlib.metadata import PackageNotFoundError, version

if len(sys.argv) > 1 and sys.argv[1] in ("-V", "--version"):
    try:
        print("mcp-server-invokeai " + version("invokeai-mcp-server"))
    except PackageNotFoundError:
        print("mcp-server-invokeai (unknown version)")
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print("Usage: mcp-server-invokeai [--version] [--help]\n\n"
          "MCP server for InvokeAI (stdio transport). Expects InvokeAI at http://127.0.0.1:9090.")
    sys.exit(0)

import invokeai_mcp_server

invokeai_mcp_server.main()
