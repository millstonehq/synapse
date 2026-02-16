#!/usr/bin/env python3
"""
Stop hook to validate /sync-docs command output.
Checks that the sync summary/completion format is followed.

Exit codes:
  0 - Valid (or not a /sync-docs session)
  2 - Invalid, stderr fed back to Claude for revision
"""
import json
import sys
import re


# Required output sections for sync-docs completion
SUMMARY_PATTERNS = [
    (r"##\s*Sync Docs Summary", "Sync Docs Summary"),
    (r"##\s*Sync Complete", "Sync Complete"),
]

# At least one of these should appear when docs are found
RESULT_PATTERNS = [
    (r"(?i)stale\s+documents?", "stale documents listing"),
    (r"(?i)changes?\s+made", "changes made listing"),
    (r"(?i)no\s+(relevant\s+)?docs", "no relevant docs message"),
    (r"(?i)no\s+stale", "no stale docs message"),
    (r"(?i)diff\s+is\s+empty", "empty diff message"),
    (r"(?i)no\s+(unstaged\s+)?changes", "no changes message"),
]

# Anti-patterns: sync-docs should NOT produce these
ANTI_PATTERNS = [
    (r"(?i)^#\s*Task\b", "Task section (this is a discover handoff, not sync-docs)"),
    (r"(?i)^#\s*Selected Code Context\b", "Selected Code Context (discover output, not sync-docs)"),
    (r"(?i)^#\s*Ambiguities\b", "Ambiguities section (discover output, not sync-docs)"),
]


def is_sync_docs_session(input_data: dict) -> bool:
    """Check if this session involves /sync-docs."""
    transcript = input_data.get("transcript_summary", "")
    if "/sync-docs" in transcript.lower():
        return True

    messages = input_data.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str) and "/sync-docs" in content.lower():
                return True
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text", "")
                        if "/sync-docs" in text.lower():
                            return True
    return False


def get_last_assistant_message(messages: list) -> str:
    """Extract last assistant text from messages."""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                return "\n".join(texts)
    return ""


def validate_sync_docs_output(output: str) -> tuple[bool, str]:
    """Validate the /sync-docs output format."""
    if not output.strip():
        return False, "No output to validate"

    # Check for anti-patterns (discover output mistakenly produced)
    for pattern, description in ANTI_PATTERNS:
        if re.search(pattern, output, re.MULTILINE):
            return False, (
                f"Output contains {description}. "
                "This looks like /discover output, not /sync-docs. "
                "Re-run with sync-docs format: Summary → Confirm → Update → Validate."
            )

    # Check that at least one summary or result section exists
    has_summary = any(
        re.search(pat, output, re.MULTILINE) for pat, _ in SUMMARY_PATTERNS
    )
    has_result = any(
        re.search(pat, output, re.MULTILINE) for pat, _ in RESULT_PATTERNS
    )

    if not has_summary and not has_result:
        return False, (
            "Output is missing sync-docs structure. Expected either:\n"
            "  - '## Sync Docs Summary' section (after analysis)\n"
            "  - '## Sync Complete' section (after updates)\n"
            "  - A clear message about no changes/no relevant docs\n"
            "Follow the sync-docs phases: detect changes → search docs → "
            "analyze staleness → propose updates → confirm → update → validate."
        )

    return True, "Valid sync-docs output"


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Prevent infinite loops
    if input_data.get("stop_hook_active"):
        sys.exit(0)

    if not is_sync_docs_session(input_data):
        sys.exit(0)

    messages = input_data.get("messages", [])
    last_output = get_last_assistant_message(messages)

    if not last_output:
        sys.exit(0)

    valid, reason = validate_sync_docs_output(last_output)

    if not valid:
        error_message = f"""
SYNC-DOCS VALIDATION FAILED: {reason}

Please revise your output to follow the /sync-docs format:
1. Show a "## Sync Docs Summary" with stale docs found
2. Ask for confirmation before editing
3. After edits, show "## Sync Complete" with changes made
4. If no changes needed, clearly state why (empty diff, no relevant docs, etc.)
"""
        print(error_message, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
