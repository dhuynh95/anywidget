# %%
# type: ignore
# ruff: noqa
# Third test: Chatbot widget with streaming
import asyncio

import anywidget
import traitlets


class ChatWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      // Container with unified background
      let container = document.createElement("div");
      container.style.cssText = "display: flex; flex-direction: column; gap: 12px; padding: 20px; max-width: 900px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;";

      // Messages container with clean, unified background
      let messagesDiv = document.createElement("div");
      messagesDiv.style.cssText = "background: #f8f9fa; border-radius: 8px; padding: 20px; max-height: 600px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px;";

      // Streaming message preview
      let streamingDiv = document.createElement("div");
      streamingDiv.style.cssText = "display: none; padding: 8px 12px; color: #6c757d; font-style: italic; font-size: 14px;";

      // Input container
      let inputContainer = document.createElement("div");
      inputContainer.style.cssText = "display: flex; gap: 8px;";

      let input = document.createElement("input");
      input.type = "text";
      input.placeholder = "Type a message...";
      input.style.cssText = "flex: 1; padding: 10px 14px; border: 1px solid #dee2e6; border-radius: 6px; font-size: 14px; outline: none; transition: border-color 0.2s;";
      input.addEventListener("focus", () => input.style.borderColor = "#007bff");
      input.addEventListener("blur", () => input.style.borderColor = "#dee2e6");

      let sendBtn = document.createElement("button");
      sendBtn.textContent = "Send";
      sendBtn.style.cssText = "padding: 10px 24px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; transition: background 0.2s;";
      sendBtn.addEventListener("mouseenter", () => sendBtn.style.background = "#0056b3");
      sendBtn.addEventListener("mouseleave", () => sendBtn.style.background = "#007bff");

      // Render messages with new clean design
      function renderMessages() {
        messagesDiv.innerHTML = "";
        let messages = model.get("messages");

        messages.forEach((msg) => {
          let msgDiv = document.createElement("div");

          // Determine message type
          let msgType = msg.type || (msg.role === "user" ? "user" : "assistant");

          // Base styling - generous spacing
          msgDiv.style.cssText = "margin-bottom: 4px;";

          // Message content container
          let contentDiv = document.createElement("div");
          contentDiv.style.cssText = "font-size: 15px; line-height: 1.6; color: #2c3e50;";

          // Style based on message type
          if (msgType === "system") {
            // System: subtle gray background, compact
            msgDiv.style.cssText += "background: #f5f5f5; padding: 12px 16px; border-radius: 6px;";
            contentDiv.style.cssText = "font-family: monospace; font-size: 12px; color: #6c757d; white-space: pre-wrap;";
            contentDiv.textContent = JSON.stringify(msg.data || msg, null, 2);
          } else if (msgType === "assistant") {
            // Assistant: no background, blends into unified background
            msgDiv.style.cssText += "padding: 4px 0;";
            contentDiv.style.cssText += "color: #2c3e50;";

            if (msg.content) {
              if (typeof msg.content === "string") {
                contentDiv.style.cssText += "white-space: pre-wrap;";
                contentDiv.textContent = msg.content;
              } else if (Array.isArray(msg.content)) {
                msg.content.forEach(block => {
                  let blockDiv = document.createElement("div");
                  blockDiv.style.cssText = "margin-top: 8px;";

                  if (block.type === "text") {
                    blockDiv.style.cssText += "white-space: pre-wrap;";
                    blockDiv.textContent = block.text;
                  } else if (block.type === "tool_use") {
                    blockDiv.style.cssText += "font-family: 'SF Mono', Monaco, monospace; font-size: 13px; color: #495057; margin: 8px 0;";
                    blockDiv.innerHTML = `<div style="color: #6c757d; font-size: 12px; margin-bottom: 4px;">→ ${block.name}</div><div style="color: #495057;">${JSON.stringify(block.input, null, 2)}</div>`;
                  } else if (block.type === "tool_result") {
                    blockDiv.style.cssText += "font-family: 'SF Mono', Monaco, monospace; font-size: 12px; color: #6c757d; white-space: pre-wrap; margin: 8px 0;";
                    let resultPreview = typeof block.content === "string"
                      ? block.content.substring(0, 300)
                      : JSON.stringify(block.content, null, 2).substring(0, 300);
                    if (resultPreview.length >= 300) resultPreview += "...";
                    blockDiv.textContent = resultPreview;
                  } else {
                    blockDiv.style.cssText += "font-family: monospace; font-size: 12px; color: #6c757d;";
                    blockDiv.textContent = JSON.stringify(block, null, 2);
                  }

                  contentDiv.appendChild(blockDiv);
                });
              }
            }
          } else if (msgType === "user") {
            // User: subtle background bubble
            msgDiv.style.cssText += "background: #e8f5e9; padding: 12px 16px; border-radius: 8px; max-width: 80%; align-self: flex-end;";
            contentDiv.style.cssText += "color: #1b5e20;";

            if (msg.content) {
              if (typeof msg.content === "string") {
                contentDiv.style.cssText += "white-space: pre-wrap;";
                contentDiv.textContent = msg.content;
              } else if (Array.isArray(msg.content)) {
                msg.content.forEach(block => {
                  let blockDiv = document.createElement("div");
                  blockDiv.style.cssText = "margin-top: 6px;";

                  if (block.type === "text") {
                    blockDiv.style.cssText += "white-space: pre-wrap;";
                    blockDiv.textContent = block.text;
                  } else if (block.type === "tool_result") {
                    blockDiv.style.cssText += "font-family: monospace; font-size: 12px; color: #2e7d32; white-space: pre-wrap; margin: 8px 0;";
                    let resultPreview = typeof block.content === "string"
                      ? block.content.substring(0, 300)
                      : JSON.stringify(block.content, null, 2).substring(0, 300);
                    if (resultPreview.length >= 300) resultPreview += "...";
                    blockDiv.textContent = resultPreview;
                  } else {
                    blockDiv.style.cssText += "font-family: monospace; font-size: 12px;";
                    blockDiv.textContent = JSON.stringify(block, null, 2);
                  }

                  contentDiv.appendChild(blockDiv);
                });
              }
            }
          }

          msgDiv.appendChild(contentDiv);
          messagesDiv.appendChild(msgDiv);
        });

        // Auto-scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
      }

      // Send message
      function sendMessage() {
        let content = input.value.trim();
        if (!content) return;

        model.send({ type: "user_message", content: content });
        input.value = "";
        sendBtn.disabled = true;
      }

      sendBtn.addEventListener("click", sendMessage);
      input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
      });

      // Listen for streaming state
      model.on("msg:custom", (msg) => {
        if (msg.type === "stream_start") {
          streamingDiv.style.display = "block";
          streamingDiv.textContent = "Assistant is thinking...";
          sendBtn.disabled = true;
        } else if (msg.type === "stream_end") {
          streamingDiv.style.display = "none";
          sendBtn.disabled = false;
        }
      });

      // Watch for messages trait changes
      model.on("change:messages", renderMessages);

      // Initial render
      renderMessages();

      // Assemble
      inputContainer.appendChild(input);
      inputContainer.appendChild(sendBtn);
      container.appendChild(messagesDiv);
      container.appendChild(streamingDiv);
      container.appendChild(inputContainer);
      el.appendChild(container);
    }
    export default { render };
    """

    messages = traitlets.List([]).tag(sync=True)

    def __init__(self, client=None, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self._is_processing = False  # Track if client is busy
        self.on_msg(self._handle_custom_msg)

    def _handle_custom_msg(self, content, buffers):
        if content.get("type") == "user_message":
            # Check if already processing a message
            if self._is_processing:
                import warnings

                warnings.warn(
                    "Message ignored: Client is busy processing previous query"
                )
                return

            user_content = content.get("content", "")
            # Add user message in Claude Code format
            self.messages = self.messages + [
                {
                    "type": "user",
                    "content": [{"type": "text", "text": user_content}],
                }
            ]
            # Schedule async response handling
            asyncio.create_task(self._handle_response(user_content))

    async def _handle_response(self, user_input):
        """Handle async client response - streams messages as they arrive."""
        from claude_code_utils import parse_messages

        self._is_processing = True
        self.send({"type": "stream_start"})

        try:
            await self.client.query(user_input)
            async for message in self.client.receive_response():
                parsed_msg = parse_messages([message])[0]
                self.messages = self.messages + [parsed_msg]
                await asyncio.sleep(0.1)  # Visual streaming delay
        finally:
            self._is_processing = False
            self.send({"type": "stream_end"})


# Mock Claude Code session messages
mock_session_messages = [
    {
        "type": "system",
        "subtype": "init",
        "data": {
            "session_id": "test-session-123",
            "model": "claude-sonnet-4-5",
            "tools": ["Bash", "Read", "Edit", "Grep"],
            "cwd": "/Users/dhuynh95/anywidget",
        },
    },
    {
        "type": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I'll help you analyze the codebase. Let me start by reading the main file.",
            }
        ],
        "model": "claude-sonnet-4-5-20250929",
        "parent_tool_use_id": None,
    },
    {
        "type": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_abc123",
                "name": "Read",
                "input": {"file_path": "/Users/dhuynh95/anywidget/playground.py"},
            }
        ],
        "model": "claude-sonnet-4-5-20250929",
        "parent_tool_use_id": None,
    },
    {
        "type": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_abc123",
                "content": "# Example file content\nimport anywidget\nimport traitlets\n\nclass MyWidget(anywidget.AnyWidget):\n    value = traitlets.Int(0).tag(sync=True)",
            }
        ],
        "parent_tool_use_id": None,
    },
    {
        "type": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I can see this is an anywidget project. The file contains a simple widget with a synchronized integer value.",
            }
        ],
        "model": "claude-sonnet-4-5-20250929",
        "parent_tool_use_id": None,
    },
]

# %%
# Test 1: Removed - now requires a client (no mock handler)

# %%
print("Test: Pre-loaded session messages (read-only view)")
session_viewer = ChatWidget(messages=mock_session_messages)
session_viewer

# %%
from typing import Any
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

MODEL = "claude-haiku-4-5"
# MODEL = "claude-sonnet-4-5"

# tools = [verify_highlighting, verify_extraction]
# name = "deep-extract-mvp"
# custom_server = create_sdk_mcp_server(
#     name=name,
#     version="0.1.0",
#     tools=tools,  # Pass the decorated function
# )
# allowed_tools = [f"mcp__{name}__{tool.name}" for tool in tools]
options = ClaudeAgentOptions(
    disallowed_tools=[
        "Task",
        "ExitPlanMode",
        "Write",
        "NotebookEdit",
        "WebFetch",
        "TodoWrite",
        "WebSearch",
        "BashOutput",
        "KillShell",
        "SlashCommand",
    ],
    allowed_tools=[
        "Bash",
        "Read",
        # "Edit", "MultiEdit"
    ],
    permission_mode="bypassPermissions",
    # system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
    # mcp_servers={},
    model=MODEL,
)

client = ClaudeSDKClient(options=options)
await client.connect()

chat = ChatWidget(client=client)
chat

# %%
chat.messages
