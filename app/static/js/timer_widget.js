const STORAGE_KEY = "learnio_active_session";

function getActiveSession() {
    const raw = localStorage.getItem(STORAGE_KEY);

    if (!raw) {
        return null;
    }

    try {
        return JSON.parse(raw);
    } catch (error) {
        console.error("Invalid timer session:", error);
        localStorage.removeItem(STORAGE_KEY);
        return null;
    }
}

function saveActiveSession(session) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

function clearActiveSession() {
    localStorage.removeItem(STORAGE_KEY);
}

function csrfHeader() {
    const tokenElement = document.querySelector(
        'meta[name="csrf-token"]'
    );

    if (!tokenElement) {
        throw new Error("CSRF token not found.");
    }

    return {
        "X-CSRFToken": tokenElement.content
    };
}


/* =========================================================
   START SESSION
   ========================================================= */

async function startFocusSession(subjectId) {

    const startBtn = document.getElementById("timer-start");
    const stopBtn = document.getElementById("timer-stop");
    const statusEl = document.getElementById("timer-status");

    if (startBtn) {
        startBtn.disabled = true;
    }

    if (statusEl) {
        statusEl.textContent = "Starting study session...";
    }

    try {

        const response = await fetch("/timer/start", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...csrfHeader()
            },
            body: JSON.stringify({
                subject_id: subjectId || null
            })
        });

        if (!response.ok) {
            const errorText = await response.text();

            throw new Error(
                `Unable to start timer (${response.status}). ${errorText}`
            );
        }

        const data = await response.json();

        if (!data.session_id) {
            throw new Error("Server did not return a session ID.");
        }

        saveActiveSession({
            sessionId: data.session_id,
            subjectId: subjectId || null,
            mode: "focus",
            phaseStartedAt: Date.now(),
            phaseDurationSeconds: POMODORO_FOCUS_SECONDS
        });

        renderAll();

    } catch (error) {

        console.error("Timer start failed:", error);

        if (statusEl) {
            statusEl.textContent =
                "Could not start the timer. Please try again.";
        }

        if (startBtn) {
            startBtn.disabled = false;
        }

    }
}


/* =========================================================
   STOP SESSION
   ========================================================= */

async function stopActiveSession() {

    const session = getActiveSession();

    if (!session) {
        renderAll();
        return;
    }

    const stopBtn = document.getElementById("timer-stop");
    const statusEl = document.getElementById("timer-status");

    if (stopBtn) {
        stopBtn.disabled = true;
    }

    try {

        if (session.mode === "focus") {

            const response = await fetch(
                `/timer/${session.sessionId}/stop`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        ...csrfHeader()
                    },
                    body: JSON.stringify({
                        completed: false
                    })
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Unable to stop timer (${response.status}).`
                );
            }
        }

        clearActiveSession();
        renderAll();

    } catch (error) {

        console.error("Timer stop failed:", error);

        if (statusEl) {
            statusEl.textContent =
                "Could not stop the timer. Please try again.";
        }

        if (stopBtn) {
            stopBtn.disabled = false;
        }
    }
}


/* =========================================================
   COMPLETE FOCUS → BREAK
   ========================================================= */

async function completeFocusPhase(session) {

    try {

        const response = await fetch(
            `/timer/${session.sessionId}/stop`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...csrfHeader()
                },
                body: JSON.stringify({
                    completed: true
                })
            }
        );

        if (!response.ok) {
            throw new Error(
                `Unable to complete timer (${response.status}).`
            );
        }

        saveActiveSession({
            ...session,
            mode: "break",
            phaseStartedAt: Date.now(),
            phaseDurationSeconds: POMODORO_BREAK_SECONDS
        });

        renderAll();

    } catch (error) {

        console.error("Timer completion failed:", error);
    }
}


function completeBreakPhase() {

    clearActiveSession();
    renderAll();
}


/* =========================================================
   TIME CALCULATIONS
   ========================================================= */

function getRemainingSeconds(session) {

    const elapsed = Math.floor(
        (Date.now() - session.phaseStartedAt) / 1000
    );

    return Math.max(
        0,
        session.phaseDurationSeconds - elapsed
    );
}


function formatTime(seconds) {

    const safeSeconds = Math.max(
        0,
        Math.floor(seconds)
    );

    const minutes = Math.floor(safeSeconds / 60);
    const remainingSeconds = safeSeconds % 60;

    return `${minutes}:${remainingSeconds
        .toString()
        .padStart(2, "0")}`;
}


/* =========================================================
   RENDER EVERYTHING
   ========================================================= */

function renderAll() {

    const session = getActiveSession();

    renderFloatingWidget(session);
    renderFullPage(session);
}


/* =========================================================
   FLOATING TIMER WIDGET
   ========================================================= */

function renderFloatingWidget(session) {

    let widget = document.getElementById(
        "floating-timer-widget"
    );

    if (!session) {

        if (widget) {
            widget.remove();
        }

        return;
    }

    /*
     * Do not display floating timer on full timer page.
     */
    if (document.getElementById("timer-display")) {

        if (widget) {
            widget.remove();
        }

        return;
    }

    if (!widget) {

        widget = document.createElement("div");

        widget.id = "floating-timer-widget";

        widget.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1050;
            background: white;
            border-radius: 12px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        `;

        document.body.appendChild(widget);
    }

    const remaining = getRemainingSeconds(session);

    const label =
        session.mode === "focus"
            ? "Focus"
            : "Break";

    const color =
        session.mode === "focus"
            ? "#2563EB"
            : "#10B981";

    widget.innerHTML = `
        <span style="
            font-weight:600;
            color:${color};
        ">
            ${label}
        </span>

        <span style="
            font-weight:700;
            font-size:1.1rem;
        ">
            ${formatTime(remaining)}
        </span>

        <button
            id="widget-stop-btn"
            type="button"
            class="btn btn-sm btn-outline"
        >
            Stop
        </button>
    `;

    const widgetStopBtn =
        document.getElementById("widget-stop-btn");

    if (widgetStopBtn) {

        widgetStopBtn.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                stopActiveSession();
            }
        );
    }
}


/* =========================================================
   FULL TIMER PAGE
   ========================================================= */

function renderFullPage(session) {

    const display =
        document.getElementById("timer-display");

    if (!display) {
        return;
    }

    const modeLabel =
        document.getElementById("timer-mode-label");

    const startBtn =
        document.getElementById("timer-start");

    const stopBtn =
        document.getElementById("timer-stop");

    const subjectSelect =
        document.getElementById("timer-subject");

    const statusEl =
        document.getElementById("timer-status");


    /* ---------- NO ACTIVE SESSION ---------- */

    if (!session) {

        display.textContent =
            formatTime(POMODORO_FOCUS_SECONDS);

        display.style.color = "#2563EB";

        if (modeLabel) {
            modeLabel.textContent = "Focus Session";
        }

        /*
         * IMPORTANT:
         * Use style.display instead of d-none.
         * The Stop button is inline-hidden in the template.
         */

        if (startBtn) {
            startBtn.style.display = "inline-flex";
            startBtn.disabled = false;
        }

        if (stopBtn) {
            stopBtn.style.display = "none";
            stopBtn.disabled = false;
        }

        if (subjectSelect) {
            subjectSelect.disabled = false;
        }

        return;
    }


    /* ---------- ACTIVE SESSION ---------- */

    const remaining =
        getRemainingSeconds(session);

    display.textContent =
        formatTime(remaining);

    display.style.color =
        session.mode === "focus"
            ? "#2563EB"
            : "#10B981";


    if (modeLabel) {

        modeLabel.textContent =
            session.mode === "focus"
                ? "Focus Session"
                : "Break";
    }


    /*
     * Explicitly switch buttons.
     */

    if (startBtn) {
        startBtn.style.display = "none";
    }

    if (stopBtn) {
        stopBtn.style.display = "inline-flex";
        stopBtn.disabled = false;
    }

    if (subjectSelect) {
        subjectSelect.disabled = true;
    }

    if (statusEl) {
        statusEl.textContent = "";
    }
}


/* =========================================================
   TIMER TICK
   ========================================================= */

setInterval(async function () {

    const session = getActiveSession();

    if (!session) {
        return;
    }

    const remaining =
        getRemainingSeconds(session);

    if (remaining <= 0) {

        if (session.mode === "focus") {

            await completeFocusPhase(session);

        } else {

            completeBreakPhase();
        }

    } else {

        renderAll();
    }

}, 1000);


/* =========================================================
   INITIALIZATION
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        renderAll();


        const startBtn =
            document.getElementById("timer-start");

        const stopBtn =
            document.getElementById("timer-stop");

        const subjectSelect =
            document.getElementById("timer-subject");


        /* ---------- START BUTTON ---------- */

        if (startBtn) {

            startBtn.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    if (startBtn.disabled) {
                        return;
                    }

                    const subjectId =
                        subjectSelect
                            ? subjectSelect.value || null
                            : null;

                    startFocusSession(subjectId);
                }
            );
        }


        /* ---------- STOP BUTTON ---------- */

        if (stopBtn) {

            stopBtn.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();

                    stopActiveSession();
                }
            );
        }


        /* ---------- LOGOUT ---------- */

        const logoutLink =
            document.getElementById("logout-link");

        if (logoutLink) {

            logoutLink.addEventListener(
                "click",
                function (event) {

                    const session =
                        getActiveSession();

                    if (!session) {
                        return;
                    }

                    event.preventDefault();

                    const confirmed =
                        window.confirm(
                            "You have an active study session running. Stop it and log out?"
                        );

                    if (!confirmed) {
                        return;
                    }

                    stopActiveSession().then(
                        function () {

                            window.location.href =
                                logoutLink.href;
                        }
                    );
                }
            );
        }

    }
);