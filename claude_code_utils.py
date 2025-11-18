from claude_agent_sdk.types import (
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)
from typing import Any


def serialize_content_block(block) -> dict[str, Any]:
    """Serialize a ContentBlock to a dictionary."""

    if isinstance(block, TextBlock):
        return {"type": "text", "text": block.text}
    elif isinstance(block, ThinkingBlock):
        return {
            "type": "thinking",
            "thinking": block.thinking,
            "signature": block.signature,
        }
    elif isinstance(block, ToolUseBlock):
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    elif isinstance(block, ToolResultBlock):
        return {
            "type": "tool_result",
            "tool_use_id": block.tool_use_id,
            "content": block.content,
            "is_error": block.is_error,
        }
    else:
        # Fallback for unknown block types
        return {"type": "unknown", "data": str(block)}


def parse_messages(messages) -> list[dict[str, Any]]:
    """Convert a list of Message objects to JSON-serializable dictionaries."""

    result = []
    for msg in messages:
        if isinstance(msg, UserMessage):
            # Handle content which can be str or list[ContentBlock]
            if isinstance(msg.content, str):
                content = msg.content
            else:
                content = [serialize_content_block(block) for block in msg.content]

            result.append(
                {
                    "type": "user",
                    "content": content,
                    "parent_tool_use_id": msg.parent_tool_use_id,
                }
            )
        elif isinstance(msg, AssistantMessage):
            result.append(
                {
                    "type": "assistant",
                    "content": [
                        serialize_content_block(block) for block in msg.content
                    ],
                    "model": msg.model,
                    "parent_tool_use_id": msg.parent_tool_use_id,
                }
            )
        elif isinstance(msg, SystemMessage):
            result.append({"type": "system", "subtype": msg.subtype, "data": msg.data})
        elif isinstance(msg, ResultMessage):
            result.append(
                {
                    "type": "result",
                    "subtype": msg.subtype,
                    "duration_ms": msg.duration_ms,
                    "duration_api_ms": msg.duration_api_ms,
                    "is_error": msg.is_error,
                    "num_turns": msg.num_turns,
                    "session_id": msg.session_id,
                    "total_cost_usd": msg.total_cost_usd,
                    "usage": msg.usage,
                    "result": msg.result,
                }
            )
        elif isinstance(msg, StreamEvent):
            result.append(
                {
                    "type": "stream_event",
                    "uuid": msg.uuid,
                    "session_id": msg.session_id,
                    "event": msg.event,
                    "parent_tool_use_id": msg.parent_tool_use_id,
                }
            )
        else:
            # Fallback for unknown message types
            result.append({"type": "unknown", "data": str(msg)})

    return result
