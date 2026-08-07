document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messagesEl = document.getElementById("chat-messages");

    const modeDescriptions = {
        study: "Study Mode only answers using your uploaded material and says so if it can't find something.",
        solve: "Solve Mode uses your material as context but can reason and generate solutions beyond it — e.g. writing code for an assignment.",
    };

    const modeLabels = { study: "📚 Study", solve: "🛠️ Solve" };

    document.querySelectorAll('input[name="chat-mode"]').forEach((radio) => {
        radio.addEventListener("change", () => {
            document.getElementById("mode-description").textContent = modeDescriptions[radio.value];
        });
    });

    function getSelectedMode() {
        const checked = document.querySelector('input[name="chat-mode"]:checked');
        return checked ? checked.value : "study";
    }

    if (!form) return;

    messagesEl.scrollTop = messagesEl.scrollHeight;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;

        const mode = getSelectedMode();
        appendMessage("user", question);
        input.value = "";
        input.disabled = true;

        const typingEl = appendTyping();

        try {
            const response = await fetch(`/chat/${CHAT_MATERIAL_ID}/send`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
                },
                body: JSON.stringify({ question, mode }),
            });

            const data = await response.json();
            typingEl.remove();

            if (data.error) {
                appendMessage("assistant", `⚠️ ${data.error}`, null, mode);
            } else {
                appendMessage("assistant", data.reply, data.sources, mode);
            }
        } catch (err) {
            typingEl.remove();
            appendMessage("assistant", "⚠️ Something went wrong. Please try again.", null, mode);
            console.error("Chat request failed:", err);
        } finally {
            input.disabled = false;
            input.focus();
        }
    });

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMessage(text) {
        // Pull out fenced code blocks FIRST and stash them, so the
        // escaping/formatting passes below never touch their contents
        // (code shouldn't have ** or * interpreted as bold/bullets).
        const codeBlocks = [];
        let working = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
            const index = codeBlocks.length;
            codeBlocks.push(escapeHtml(code.trim()));
            return `\u0000CODEBLOCK${index}\u0000`;
        });

        let safe = escapeHtml(working);

        safe = safe.replace(/^### (.+)$/gm, "<strong class='d-block mt-2 mb-1'>$1</strong>");
        safe = safe.replace(/^## (.+)$/gm, "<strong class='d-block mt-2 mb-1' style='font-size:1.05em'>$1</strong>");
        safe = safe.replace(/^# (.+)$/gm, "<strong class='d-block mt-2 mb-1' style='font-size:1.1em'>$1</strong>");
        safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        safe = safe.replace(/`(.+?)`/g, "<code>$1</code>");
        safe = safe.replace(/\n\s*\*\s+(.+)/g, "<br>&bull; $1");
        safe = safe.replace(/\n/g, "<br>");

        // Restore code blocks as proper <pre><code> elements
        safe = safe.replace(/\u0000CODEBLOCK(\d+)\u0000/g, (match, index) => {
            return `<pre class="bg-dark text-light p-2 rounded mt-2 mb-2" style="overflow-x:auto;"><code>${codeBlocks[index]}</code></pre>`;
        });

        return safe;
    }

    function appendMessage(role, content, sources, mode) {
        const emptyState = messagesEl.querySelector(".text-center.text-muted");
        if (emptyState) emptyState.remove();

        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${role}`;
        bubble.innerHTML = formatMessage(content);

        if (role === "assistant" && mode) {
            const modeTag = document.createElement("div");
            modeTag.className = "chat-sources";
            modeTag.textContent = modeLabels[mode] || mode;
            bubble.insertBefore(modeTag, bubble.firstChild);
        }

        if (role === "assistant" && sources && sources.length > 0) {
            const sourceEl = document.createElement("div");
            sourceEl.className = "chat-sources";
            sourceEl.textContent = `Sources: ${sources.join(", ")}`;
            bubble.appendChild(sourceEl);
        }

        messagesEl.appendChild(bubble);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function appendTyping() {
        const el = document.createElement("div");
        el.className = "chat-typing";
        el.textContent = "Thinking…";
        messagesEl.appendChild(el);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return el;
    }
});