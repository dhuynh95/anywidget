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
      container.style.cssText = "display: flex; flex-direction: column; gap: 10px; padding: 10px; max-width: 600px; font-family: sans-serif;";

      // Messages container
      let messagesDiv = document.createElement("div");
      messagesDiv.style.cssText = "border: 1px solid #ccc; border-radius: 5px; padding: 10px; max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;";

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

      // Render messages from trait
      function renderMessages() {
        messagesDiv.innerHTML = "";
        let messages = model.get("messages");
        messages.forEach(msg => {
          let msgEl = document.createElement("div");
          msgEl.style.cssText = `padding: 8px; border-radius: 5px; ${msg.role === "user" ? "background: #e3f2fd; align-self: flex-end;" : "background: #f5f5f5; align-self: flex-start;"}`;
          msgEl.innerHTML = `<strong>${msg.role}:</strong> ${msg.content}`;
          messagesDiv.appendChild(msgEl);
        });
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_msg(self._handle_custom_msg)

    def _handle_custom_msg(self, content, buffers):
        if content.get("type") == "user_message":
            user_content = content.get("content", "")
            # Add user message to history
            self.messages = self.messages + [{"role": "user", "content": user_content}]
            # Start streaming response in background thread
            threading.Thread(target=self._stream_response, daemon=True).start()

    def _stream_response(self):
        """Stream complete messages one by one"""
        self.send({"type": "stream_start"})

        # Stream each message as it's yielded
        for message in self._mock_chat_handler():
            self.messages = self.messages + [message]
            time.sleep(0.5)  # Delay between messages for visual effect

        self.send({"type": "stream_end"})

    def _mock_chat_handler(self):
        """Mock streaming chat handler that yields discrete messages"""
        # Simulate multi-step response like tool use
        yield {"role": "assistant", "content": "Let me check the weather for you..."}
        yield {"role": "assistant", "content": "🔧 Calling weather API..."}
        yield {
            "role": "assistant",
            "content": "📊 Got results: Temperature 72°F, Sunny",
        }
        yield {
            "role": "assistant",
            "content": "The weather is sunny today with a temperature of 72°F!",
        }


class ClaudeSessionWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let container = document.createElement("div");
      container.style.cssText = "font-family: monospace; max-width: 900px; padding: 10px;";

      function renderMessages() {
        container.innerHTML = "";
        let messages = model.get("messages");

        messages.forEach((msg, idx) => {
          let msgDiv = document.createElement("div");
          msgDiv.style.cssText = `margin-bottom: 15px; padding: 10px; border-radius: 5px; border-left: 4px solid;`;

          // Style based on message type
          if (msg.type === "system") {
            msgDiv.style.backgroundColor = "#f5f5f5";
            msgDiv.style.borderColor = "#999";
          } else if (msg.type === "assistant") {
            msgDiv.style.backgroundColor = "#e3f2fd";
            msgDiv.style.borderColor = "#2196f3";
          } else if (msg.type === "user") {
            msgDiv.style.backgroundColor = "#f1f8e9";
            msgDiv.style.borderColor = "#8bc34a";
          }

          // Message header
          let header = document.createElement("div");
          header.style.cssText = "font-weight: bold; margin-bottom: 8px; color: #333;";
          header.textContent = `[${idx + 1}] ${msg.type.toUpperCase()}`;
          msgDiv.appendChild(header);

          // Message content
          let content = document.createElement("div");
          content.style.cssText = "white-space: pre-wrap; font-size: 13px;";

          if (msg.type === "system") {
            content.textContent = JSON.stringify(msg.data || msg, null, 2);
          } else if (msg.content) {
            if (typeof msg.content === "string") {
              content.textContent = msg.content;
            } else if (Array.isArray(msg.content)) {
              msg.content.forEach(block => {
                let blockDiv = document.createElement("div");
                blockDiv.style.cssText = "margin-top: 8px; padding: 8px; background: rgba(0,0,0,0.05); border-radius: 3px;";

                if (block.type === "text") {
                  blockDiv.innerHTML = `<strong>[text]</strong><br>${block.text}`;
                } else if (block.type === "tool_use") {
                  blockDiv.innerHTML = `<strong>[tool_use: ${block.name}]</strong><br>id: ${block.id}<br>input: ${JSON.stringify(block.input, null, 2)}`;
                } else if (block.type === "tool_result") {
                  let resultPreview = JSON.stringify(block.content, null, 2).substring(0, 200) + "...";
                  blockDiv.innerHTML = `<strong>[tool_result]</strong><br>tool_use_id: ${block.tool_use_id}<br>preview: ${resultPreview}`;
                } else {
                  blockDiv.textContent = JSON.stringify(block, null, 2);
                }

                content.appendChild(blockDiv);
              });
            }
          }

          msgDiv.appendChild(content);
          container.appendChild(msgDiv);
        });
      }

      model.on("change:messages", renderMessages);
      renderMessages();
      el.appendChild(container);
    }
    export default { render };
    """

    messages = traitlets.List([]).tag(sync=True)


print("Testing ChatWidget with streaming...")
chat = ChatWidget()
chat

# %%
chat.messages = chat.messages + [{"role": "assistant", "content": "Injected message!"}]
# %%
chat.messages = [
    {"role": "user", "content": "What's 2+2?"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "What about 3+3?"},
]
chat
# %%

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
print("Testing ClaudeSessionWidget...")
session_viewer = ClaudeSessionWidget(messages=mock_session_messages)
session_viewer
# %%
