document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messagesEl = document.getElementById("chat-messages");

    if (!form) return;

    // Scroll to the latest message on load
    messagesEl.scrollTop = messagesEl.scrollHeight;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;

        appendMessage("user", question);
        input.value = "";
        input.disabled = true;

        const typingEl = appendTyping();

        try {
            const response = await fetch(`/chat/${CHAT_SUBJECT_ID}/send`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
                },
                body: JSON.stringify({ question }),
            });

            const data = await response.json();
            typingEl.remove();

            if (data.error) {
                appendMessage("assistant", `⚠️ ${data.error}`);
            } else {
                appendMessage("assistant", data.reply, data.sources);
            }
        } catch (err) {
            typingEl.remove();
            appendMessage("assistant", "⚠️ Something went wrong. Please try again.");
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
        // Escape first — nothing in the raw AI/user text is ever trusted
        // as real HTML. Only AFTER escaping do we selectively re-introduce
        // a small, safe set of formatting tags ourselves.
        let safe = escapeHtml(text);

        safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");   // **bold**
        safe = safe.replace(/`(.+?)`/g, "<code>$1</code>");             // `code`
        safe = safe.replace(/\n\s*\*\s+(.+)/g, "<br>&bull; $1");        // * bullet lines
        safe = safe.replace(/\n/g, "<br>");                             // remaining newlines

        return safe;
    }

    function appendMessage(role, content, sources) {
        // Clear the "no messages yet" empty state on first real message
        const emptyState = messagesEl.querySelector(".text-center.text-muted");
        if (emptyState) emptyState.remove();

        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${role}`;
        bubble.innerHTML = formatMessage(content);

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