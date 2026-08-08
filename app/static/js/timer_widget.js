const STORAGE_KEY = "learnio_active_session";

function getActiveSession() {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
}

function saveActiveSession(session) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

function clearActiveSession() {
    localStorage.removeItem(STORAGE_KEY);
}

function csrfHeader() {
    return { "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content };
}

// ===== Starting / stopping (shared by both the widget and the full page) =====

async function startFocusSession(subjectId) {
    const response = await fetch("/timer/start", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...csrfHeader() },
        body: JSON.stringify({ subject_id: subjectId || null }),
    });
    const data = await response.json();

    saveActiveSession({
        sessionId: data.session_id,
        subjectId: subjectId || null,
        mode: "focus",
        phaseStartedAt: Date.now(),
        phaseDurationSeconds: POMODORO_FOCUS_SECONDS,
    });

    renderAll();
}

async function stopActiveSession() {
    const session = getActiveSession();
    if (!session) return;

    if (session.mode === "focus") {
        await fetch(`/timer/${session.sessionId}/stop`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...csrfHeader() },
            body: JSON.stringify({ completed: false }),
        });
    }
    // Breaks were never logged as a StudySession in the first place —
    // nothing to stop server-side, just clear local state.

    clearActiveSession();
    renderAll();
}

async function completeFocusPhase(session) {
    await fetch(`/timer/${session.sessionId}/stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...csrfHeader() },
        body: JSON.stringify({ completed: true }),
    });

    saveActiveSession({
        ...session,
        mode: "break",
        phaseStartedAt: Date.now(),
        phaseDurationSeconds: POMODORO_BREAK_SECONDS,
    });
    renderAll();
}

function completeBreakPhase() {
    clearActiveSession();
    renderAll();
}

// ===== Rendering — recomputes remaining time from real timestamps, =====
// ===== so it's always correct even after a page navigation. =====

function getRemainingSeconds(session) {
    const elapsed = Math.floor((Date.now() - session.phaseStartedAt) / 1000);
    return Math.max(0, session.phaseDurationSeconds - elapsed);
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
}

function renderAll() {
    const session = getActiveSession();
    renderFloatingWidget(session);
    renderFullPage(session);
}

function renderFloatingWidget(session) {
    let widget = document.getElementById("floating-timer-widget");

    if (!session) {
        if (widget) widget.remove();
        return;
    }

    // Don't show the floating widget ON the full timer page itself —
    // that would be a redundant second countdown on the same screen.
    if (document.getElementById("timer-display")) {
        if (widget) widget.remove();
        return;
    }

    if (!widget) {
        widget = document.createElement("div");
        widget.id = "floating-timer-widget";
        widget.className = "shadow-sm";
        widget.style.cssText = `
            position: fixed; bottom: 20px; right: 20px; z-index: 1050;
            background: white; border-radius: 12px; padding: 12px 16px;
            display: flex; align-items: center; gap: 10px;
            border: 1px solid #E2E8F0;
        `;
        document.body.appendChild(widget);
    }

    const remaining = getRemainingSeconds(session);
    const label = session.mode === "focus" ? "Focus" : "Break";
    const color = session.mode === "focus" ? "#2563EB" : "#10B981";

    widget.innerHTML = `
        <span style="font-weight:600; color:${color};">${label}</span>
        <span style="font-weight:700; font-size:1.1rem;">${formatTime(remaining)}</span>
        <button id="widget-stop-btn" class="btn btn-sm btn-outline-danger">Stop</button>
    `;
    document.getElementById("widget-stop-btn").addEventListener("click", stopActiveSession);
}

function renderFullPage(session) {
    const display = document.getElementById("timer-display");
    if (!display) return; // not on the /timer page

    const modeLabel = document.getElementById("timer-mode-label");
    const startBtn = document.getElementById("timer-start");
    const stopBtn = document.getElementById("timer-stop");
    const subjectSelect = document.getElementById("timer-subject");
    const statusEl = document.getElementById("timer-status");

    if (!session) {
        display.textContent = formatTime(POMODORO_FOCUS_SECONDS);
        display.style.color = "#2563EB";
        modeLabel.textContent = "Focus Session";
        startBtn.classList.remove("d-none");
        stopBtn.classList.add("d-none");
        subjectSelect.disabled = false;
        return;
    }

    const remaining = getRemainingSeconds(session);
    display.textContent = formatTime(remaining);
    display.style.color = session.mode === "focus" ? "#2563EB" : "#10B981";
    modeLabel.textContent = session.mode === "focus" ? "Focus Session" : "Break";
    startBtn.classList.add("d-none");
    stopBtn.classList.remove("d-none");
    subjectSelect.disabled = true;

    if (statusEl) statusEl.textContent = "";
}

// ===== Tick loop — checks every second, handles phase transitions =====

setInterval(() => {
    const session = getActiveSession();
    if (!session) return;

    const remaining = getRemainingSeconds(session);
    if (remaining <= 0) {
        if (session.mode === "focus") {
            completeFocusPhase(session);
        } else {
            completeBreakPhase();
        }
    } else {
        renderAll();
    }
}, 1000);

// ===== Logout interception =====

document.addEventListener("DOMContentLoaded", () => {
    renderAll();

    const startBtn = document.getElementById("timer-start");
    const stopBtn = document.getElementById("timer-stop");
    const subjectSelect = document.getElementById("timer-subject");

    if (startBtn) {
        startBtn.addEventListener("click", () => startFocusSession(subjectSelect.value || null));
    }
    if (stopBtn) {
        stopBtn.addEventListener("click", stopActiveSession);
    }

    const logoutLink = document.getElementById("logout-link");
    if (logoutLink) {
        logoutLink.addEventListener("click", (e) => {
            const session = getActiveSession();
            if (!session) return; // no active session — let logout proceed normally

            e.preventDefault();
            const confirmed = confirm(
                "You have an active study session running. Stop it and log out?"
            );
            if (confirmed) {
                stopActiveSession().then(() => {
                    window.location.href = logoutLink.href;
                });
            }
        });
    }

    
});