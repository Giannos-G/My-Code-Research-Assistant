"""Interactive chat loop for the code research assistant agent."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from . import db, mcp_client, tools

GITHUB_MODELS_URL = "https://models.github.ai/inference"

SYSTEM_PROMPT = (
    "You are a code research assistant. You can search and read code across "
    "public GitHub repositories and search the live web for documentation, "
    "blog posts, and discussions. When asked how something is implemented, "
    "look it up with your tools and cite what you found instead of "
    "guessing. You can also check list_past_research for earlier answers. "
    "Keep replies concise and include repo/file references when relevant."
)


def _build_client() -> OpenAI:
    token = os.environ.get("GITHUB_MODELS_TOKEN")
    if not token:
        raise SystemExit(
            "GITHUB_MODELS_TOKEN is not set. Create a GitHub PAT with the "
            "'models' permission and put it in your .env file (see .env.example)."
        )
    return OpenAI(base_url=GITHUB_MODELS_URL, api_key=token)


async def _run_turn(
    client: OpenAI,
    model: str,
    messages: list[dict],
    all_tools: list[dict],
    multi: mcp_client.MultiMCP,
) -> str:
    """Send messages to the model, executing any tool calls it requests,
    until it produces a final text reply."""
    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=all_tools,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content})
            return message.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
            }
        )

        for call in message.tool_calls:
            arguments = json.loads(call.function.arguments or "{}")
            local_result = tools.dispatch_local(call.function.name, arguments)
            if local_result is not None:
                result = local_result
            else:
                result = await multi.call_tool(call.function.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )


async def main() -> None:
    load_dotenv()
    db.init_db()

    client = _build_client()
    model = os.environ.get("MODEL_NAME", "openai/gpt-4o-mini")

    multi = await mcp_client.connect_all()
    if not multi.openai_tools:
        print(
            "Warning: no MCP servers connected (set GITHUB_MCP_TOKEN and/or "
            "EXA_API_KEY in .env). Only local history lookup will work."
        )
    all_tools = multi.openai_tools + [tools.HISTORY_TOOL]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("My Code Research Assistant — ask a question. Type 'exit' to quit.")
    try:
        while True:
            try:
                user_input = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break

            messages.append({"role": "user", "content": user_input})
            reply = await _run_turn(client, model, messages, all_tools, multi)
            print(f"assistant> {reply}")
            db.log_research(user_input, reply)
    finally:
        await multi.aclose()
