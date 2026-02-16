#!/usr/bin/env python3
"""
Stop hook to validate /discover command output.
Checks that the handoff prompt format is followed.

Exit codes:
  0 - Valid (or not a /discover session)
  2 - Invalid, stderr fed back to Claude for revision
"""
import json
import sys
import re

REQUIRED_SECTIONS = [
    (r"#\s*Task\b", "Task"),
    (r"#\s*Architecture\b", "Architecture"),
    (r"#\s*Selected Code Context\b", "Selected Code Context"),
    (r"#\s*Relationships\b", "Relationships"),
    (r"#\s*Ambiguities\b", "Ambiguities"),
]

# Patterns that indicate analysis instead of handoff (anti-patterns)
# These suggest Claude went straight to analysis without the handoff structure
ANALYSIS_PATTERNS = [
    (r"(?i)here('s| is) (my |the |an )?analysis", "direct analysis"),
    (r"(?i)^##\s*(key )?(improvements?|recommendations?)", "recommendations header"),
    (r"(?i)^###\s*\d+\.\s*\*\*", "numbered improvement list"),  # ### 1. **Something**
    (r"(?i)summary:?\s*$\n\n.*strengths", "analysis summary format"),
]


def is_discover_session(input_data: dict) -> bool:
    """Check if this session involved /discover command."""
    # Check transcript summary
    transcript = input_data.get("transcript_summary", "")
    if "/discover" in transcript.lower():
        return True

    # Check messages for command invocation
    messages = input_data.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str) and "/discover" in content.lower():
                return True
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text", "")
                        if "/discover" in text.lower():
                            return True

    return False


def get_last_assistant_message(messages: list) -> str:
    """Extract the last assistant message text."""
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


def validate_discover_output(output: str) -> tuple[bool, str]:
    """Validate that output follows handoff prompt format."""
    if not output.strip():
        return False, "No output to validate"

    # Check for required sections
    missing = []
    for pattern, name in REQUIRED_SECTIONS:
        if not re.search(pattern, output, re.MULTILINE):
            missing.append(name)

    if missing:
        return False, f"Missing required sections: {', '.join(missing)}"

    # Check for analysis anti-patterns
    for pattern, description in ANALYSIS_PATTERNS:
        if re.search(pattern, output, re.MULTILINE):
            return False, f"Output appears to be {description} rather than a handoff prompt"

    # Check for inline code (should have code blocks in Selected Code Context)
    # At minimum, need opening and closing backticks
    code_block_count = len(re.findall(r"```", output))
    if code_block_count < 2:
        return False, "Handoff prompt should include inline code in Selected Code Context section"

    return True, "Valid handoff prompt"


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Can't parse input, don't block
        sys.exit(0)

    # Check for stop_hook_active to prevent loops
    if input_data.get("stop_hook_active"):
        sys.exit(0)

    # Only validate /discover sessions
    if not is_discover_session(input_data):
        sys.exit(0)

    # Get the last assistant message
    messages = input_data.get("messages", [])
    last_output = get_last_assistant_message(messages)

    if not last_output:
        sys.exit(0)

    # Validate the output
    valid, reason = validate_discover_output(last_output)

    if not valid:
        # Exit code 2 feeds stderr back to Claude for automatic revision
        error_message = f"""
DISCOVER VALIDATION FAILED: {reason}

The /discover command requires a structured handoff prompt with these sections:
- # Task
- # Architecture
- # Selected Code Context (with inline code)
- # Relationships
- # Ambiguities

Please revise your output to follow this format. Do not provide direct analysis or recommendations without the handoff structure.

If the user's request was for analysis rather than implementation context, you should have asked them first whether they wanted:
A) A handoff prompt (what /discover produces)
B) Direct analysis (which requires a different approach)
"""
        print(error_message, file=sys.stderr)
        sys.exit(2)

    # Valid output
    sys.exit(0)


if __name__ == "__main__":
    main()
