# %%
# Third test: Chatbot widget with streaming
import threading
import time

import anywidget
import traitlets


class ChatWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      // Container
      let container = document.createElement("div");
      container.style.cssText = "display: flex; flex-direction: column; gap: 10px; padding: 10px; max-width: 900px; font-family: sans-serif;";

      // Messages container
      let messagesDiv = document.createElement("div");
      messagesDiv.style.cssText = "border: 1px solid #ccc; border-radius: 5px; padding: 10px; max-height: 500px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;";

      // Streaming message preview
      let streamingDiv = document.createElement("div");
      streamingDiv.style.cssText = "display: none; padding: 8px; background: #f0f0f0; border-radius: 5px; font-style: italic;";

      // Input container
      let inputContainer = document.createElement("div");
      inputContainer.style.cssText = "display: flex; gap: 5px;";

      let input = document.createElement("input");
      input.type = "text";
      input.placeholder = "Type a message...";
      input.style.cssText = "flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 5px;";

      let sendBtn = document.createElement("button");
      sendBtn.textContent = "Send";
      sendBtn.style.cssText = "padding: 8px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;";

      // Render messages with Claude Code format support
      function renderMessages() {
        messagesDiv.innerHTML = "";
        let messages = model.get("messages");

        messages.forEach((msg, idx) => {
          let msgDiv = document.createElement("div");
          msgDiv.style.cssText = "padding: 10px; border-radius: 5px; border-left: 4px solid;";

          // Determine message type (support both 'type' and 'role' fields)
          let msgType = msg.type || (msg.role === "user" ? "user" : "assistant");

          // Style based on message type
          if (msgType === "system") {
            msgDiv.style.backgroundColor = "#f5f5f5";
            msgDiv.style.borderColor = "#999";
          } else if (msgType === "assistant") {
            msgDiv.style.backgroundColor = "#e3f2fd";
            msgDiv.style.borderColor = "#2196f3";
          } else if (msgType === "user") {
            msgDiv.style.backgroundColor = "#f1f8e9";
            msgDiv.style.borderColor = "#8bc34a";
          }

          // Message header with number and type
          let header = document.createElement("div");
          header.style.cssText = "font-weight: bold; margin-bottom: 8px; color: #333; font-size: 12px;";
          header.textContent = `[${idx + 1}] ${msgType.toUpperCase()}`;
          msgDiv.appendChild(header);

          // Message content
          let contentDiv = document.createElement("div");
          contentDiv.style.cssText = "font-size: 14px;";

          // Handle different content formats
          if (msgType === "system") {
            // System messages show data
            contentDiv.style.cssText += "white-space: pre-wrap; font-family: monospace; font-size: 12px;";
            contentDiv.textContent = JSON.stringify(msg.data || msg, null, 2);
          } else if (msg.content) {
            // Handle string content (simple format)
            if (typeof msg.content === "string") {
              contentDiv.style.cssText += "white-space: pre-wrap;";
              contentDiv.textContent = msg.content;
            }
            // Handle array of content blocks (Claude Code format)
            else if (Array.isArray(msg.content)) {
              msg.content.forEach(block => {
                let blockDiv = document.createElement("div");
                blockDiv.style.cssText = "margin-top: 6px;";

                if (block.type === "text") {
                  blockDiv.style.cssText += "white-space: pre-wrap;";
                  blockDiv.textContent = block.text;
                } else if (block.type === "tool_use") {
                  blockDiv.style.cssText += "padding: 8px; background: rgba(0,0,0,0.05); border-radius: 3px; font-family: monospace; font-size: 12px;";
                  blockDiv.innerHTML = `<strong>[tool_use: ${block.name}]</strong><br>id: ${block.id}<br>input: ${JSON.stringify(block.input, null, 2)}`;
                } else if (block.type === "tool_result") {
                  blockDiv.style.cssText += "padding: 8px; background: rgba(0,0,0,0.05); border-radius: 3px; font-family: monospace; font-size: 12px; white-space: pre-wrap;";
                  let resultPreview = typeof block.content === "string"
                    ? block.content.substring(0, 300)
                    : JSON.stringify(block.content, null, 2).substring(0, 300);
                  if (resultPreview.length >= 300) resultPreview += "...";
                  blockDiv.innerHTML = `<strong>[tool_result]</strong><br>${resultPreview}`;
                } else {
                  blockDiv.style.cssText += "padding: 8px; background: rgba(0,0,0,0.05); border-radius: 3px; font-family: monospace; font-size: 12px;";
                  blockDiv.textContent = JSON.stringify(block, null, 2);
                }

                contentDiv.appendChild(blockDiv);
              });
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

    def __init__(self, handler=None, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler or self._mock_chat_handler
        self.on_msg(self._handle_custom_msg)

    def _handle_custom_msg(self, content, buffers):
        if content.get("type") == "user_message":
            user_content = content.get("content", "")
            # Add user message in Claude Code format
            self.messages = self.messages + [
                {
                    "type": "user",
                    "content": [{"type": "text", "text": user_content}],
                }
            ]
            # Start streaming response in background thread
            threading.Thread(target=self._stream_response, daemon=True).start()

    def _stream_response(self):
        """Stream complete messages one by one."""
        self.send({"type": "stream_start"})

        # Stream each message as it's yielded from handler
        for message in self.handler():
            self.messages = self.messages + [message]
            time.sleep(0.5)  # Delay between messages for visual effect

        self.send({"type": "stream_end"})

    def _mock_chat_handler(self):
        """Mock streaming chat handler that yields Claude Code format messages."""
        # Simulate multi-step response like tool use
        yield {
            "type": "assistant",
            "content": [
                {"type": "text", "text": "Let me check the weather for you..."}
            ],
        }
        yield {
            "type": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_weather_123",
                    "name": "get_weather",
                    "input": {"location": "current"},
                }
            ],
        }
        yield {
            "type": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_weather_123",
                    "content": '{"temperature": 72, "condition": "Sunny"}',
                }
            ],
        }
        yield {
            "type": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "The weather is sunny today with a temperature of 72°F!",
                }
            ],
        }


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
print("Test 1: Interactive chat with streaming (type a message)")
chat = ChatWidget()
chat

# %%


print("Test 2: Pre-loaded session messages (read-only view)")
session_viewer = ChatWidget(messages=mock_session_messages)
session_viewer
# %%
