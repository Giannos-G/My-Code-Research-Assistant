"""The one local tool (research history) exposed alongside the MCP tools."""

from . import db

HISTORY_TOOL = {
    "type": "function",
    "function": {
        "name": "list_past_research",
        "description": (
            "List previously answered research questions from the local "
            "history log, optionally filtered by keyword."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Only return entries matching this keyword.",
                }
            },
        },
    },
}


def dispatch_local(name: str, arguments: dict) -> str | None:
    """Handle the local history tool. Returns None if name isn't ours."""
    if name != "list_past_research":
        return None

    rows = db.list_past_research(arguments.get("keyword"))
    if not rows:
        return "No past research found."
    lines = [f"- [{r['created_at']}] {r['question']}\n  {r['answer']}" for r in rows]
    return "\n".join(lines)
