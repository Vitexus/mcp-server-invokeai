# InvokeAI MCP Server Troubleshooting Log

## Current Status: ✅ RESOLVED - SERVER NOW WORKING

### What We Built
1. **MCP Server**: `/home/cdm/invokeai-cmp/invokeai_mcp_server.py`
   - Server initializes correctly when tested directly
   - Provides tools: `generate_image`, `list_models`, `get_queue_status`
   - Successfully generates images when tested standalone

2. **Correct Configuration**: `~/.claude.json` (NOT ~/.config/claude-code/.mcp.json)
   - Registered using CLI command: `claude mcp add --scope user invokeai <command> <args>`
   - Server now appears in `claude mcp list` output

### The Problem We Had ❌
**ROOT CAUSE**: We were editing the WRONG config file!
- ❌ We edited: `~/.config/claude-code/.mcp.json`
- ✅ Correct location: `~/.claude.json`

When typing `/mcp` in Claude Code, only `plugin:testing-suite:playwright-server` appeared:
- The `invokeai` server was NOT listed
- Restarting Claude Code didn't help
- Manual config file edits were being ignored

### The Solution ✅
**Use the Claude CLI command instead of manually editing config files:**

```bash
claude mcp add --scope user invokeai /home/cdm/invokeai-cmp/venv/bin/python /home/cdm/invokeai-cmp/invokeai_mcp_server.py
```

This command:
1. Adds the server to the correct config file (`~/.claude.json`)
2. Registers it properly in Claude Code's MCP system
3. Makes it available across all projects (user scope)

### Verification ✅
After adding the server, verify it's working:

```bash
claude mcp list
```

Expected output:
```
Checking MCP server health...

plugin:testing-suite:playwright-server: npx @playwright/mcp@latest - ✓ Connected
invokeai: /home/cdm/invokeai-cmp/venv/bin/python /home/cdm/invokeai-cmp/invokeai_mcp_server.py - ✓ Connected
```

### Using the Server
**IMPORTANT**: After registering a new MCP server, you must:
1. Start a new Claude Code conversation, OR
2. Restart Claude Code

The server won't be available in existing conversations. Once restarted, Claude will have access to these tools:
- `mcp__invokeai__generate_image` - Generate images from text prompts
- `mcp__invokeai__list_models` - List available AI models
- `mcp__invokeai__get_queue_status` - Check processing queue status

### Key Lessons Learned

1. **Always use the CLI for MCP server registration**
   - Don't manually edit config files
   - Use `claude mcp add` command instead
   - This ensures proper registration in the correct location

2. **Config File Locations**
   - ✅ User scope: `~/.claude.json` (used by `claude mcp add --scope user`)
   - ✅ Project scope: `<project>/.mcp.json` (used by `claude mcp add --scope project`)
   - ❌ NOT: `~/.config/claude-code/.mcp.json` (wrong location!)

3. **Testing the Server**
   - Test server initialization manually:
     ```bash
     echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | /home/cdm/invokeai-cmp/venv/bin/python /home/cdm/invokeai-cmp/invokeai_mcp_server.py
     ```
   - Check registration: `claude mcp list`
   - Verify health: Look for `✓ Connected` status

4. **MCP Server Scopes**
   - `--scope user`: Available across all projects
   - `--scope project`: Only available in current project
   - `--scope local`: Project-specific, private to user (default)

## Environment Details
- OS: Linux (WSL2)
- Working Directory: `/home/cdm/invokeai-cmp`
- Python: venv at `/home/cdm/invokeai-cmp/venv`
- InvokeAI: Running on `http://127.0.0.1:9090`
- Config: `~/.claude.json` (user scope)

## Timeline
- **Initial setup**: Created server script and config
- **Problem discovered**: Manually edited `~/.config/claude-code/.mcp.json` (wrong file!)
- **Multiple restart attempts**: Server still not appearing (config file was wrong)
- **Root cause found**: Claude Code uses `~/.claude.json`, not `~/.config/claude-code/.mcp.json`
- **Solution applied**: Used `claude mcp add --scope user` CLI command
- **Status**: ✅ **RESOLVED** - Server now appears in `claude mcp list` with `✓ Connected` status

## Quick Reference

### To Add the Server (if needed again):
```bash
claude mcp add --scope user invokeai /home/cdm/invokeai-cmp/venv/bin/python /home/cdm/invokeai-cmp/invokeai_mcp_server.py
```

### To Check Server Status:
```bash
claude mcp list
```

### To Remove the Server (if needed):
```bash
claude mcp remove invokeai
```

### Server Configuration:
- **Name**: invokeai
- **Python**: `/home/cdm/invokeai-cmp/venv/bin/python`
- **Script**: `/home/cdm/invokeai-cmp/invokeai_mcp_server.py`
- **InvokeAI Backend**: `http://127.0.0.1:9090`
