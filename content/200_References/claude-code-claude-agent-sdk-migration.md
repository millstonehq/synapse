---
id: claude-agent-sdk-migration
type: reference
title: "Claude Agent SDK Migration"
status: published
owner: automation
created: "2025-10-29T00:00:00.000Z"
updated: "2025-10-29T00:00:00.000Z"
upstream_url: https://docs.claude.com/en/docs/claude-code
last_synced: "2025-10-29T00:00:00.000Z"
attribution: "Anthropic"
license: "Anthropic Documentation License"
category: documentation
tags: [reference, claude, agent-sdk, migration]
summary: Guide for migrating from Claude Code SDK to Claude Agent SDK, including package name changes and breaking changes.
---

## Overview

The Claude Code SDK has been renamed to the **Claude Agent SDK** to better reflect its expanded capabilities beyond coding tasks.

## Key Changes

| Aspect | Old | New |
|--------|-----|-----|
| **TS/JS Package** | `@anthropic-ai/claude-code` | `@anthropic-ai/claude-agent-sdk` |
| **Python Package** | `claude-code-sdk` | `claude-agent-sdk` |
| **Documentation** | Claude Code docs | API Guide → Agent SDK section |

## Migration Instructions

### TypeScript/JavaScript

- Uninstall: `npm uninstall @anthropic-ai/claude-code`
- Install: `npm install @anthropic-ai/claude-agent-sdk`
- Update imports from `@anthropic-ai/claude-code` to `@anthropic-ai/claude-agent-sdk`

### Python

- Uninstall: `pip uninstall claude-code-sdk`
- Install: `pip install claude-agent-sdk`
- Update imports: `claude_code_sdk` → `claude_agent_sdk`
- Rename type: `ClaudeCodeOptions` → `ClaudeAgentOptions`

## Breaking Changes

1. **System Prompt**: No longer defaults to Claude Code's prompt; explicitly specify or use the `"claude_code"` preset
2. **Settings Sources**: Filesystem settings no longer load automatically; use `settingSources` option if needed
3. **Python Type Rename**: `ClaudeCodeOptions` becomes `ClaudeAgentOptions` for consistency

## Rationale

The rename reflects the SDK's evolution from a coding-focused tool to a comprehensive framework for building agents across various domains—business, specialized coding, and custom applications.

## See Also

- [Official Claude Agent SDK Documentation](https://docs.claude.com/en/docs/claude-agent-sdk)
