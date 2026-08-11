// ===== File processing (Phase 3, Step 2) =====

async function processMaterial(materialId) {
    const badge = document.getElementById(`status-${materialId}`);
    if (!badge) return;

    try {
        const response = await fetch(`/materials/${materialId}/process`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content },
        });
        const data = await response.json();
        updateBadge(badge, data.status);

        if (data.status === "processing") {
            pollStatus(materialId, badge);
        } else if (data.status === "ready") {
            revealSummaryControls(materialId);
        }
    } catch (err) {
        console.error("Failed to start processing:", err);
    }
}

async function pollStatus(materialId, badge) {
    const interval = setInterval(async () => {
        const response = await fetch(`/materials/${materialId}/status`);
        const data = await response.json();
        updateBadge(badge, data.status);

        if (data.status === "ready" || data.status === "failed") {
            clearInterval(interval);
            if (data.status === "ready") {
                revealSummaryControls(materialId);
            }
        }
    }, 2000);
}

function revealSummaryControls(materialId) {
    const summaryControls = document.getElementById(`summary-controls-${materialId}`);
    if (summaryControls) summaryControls.classList.remove("d-none");
}

function updateBadge(badge, status) {
    const labels = { pending: "Pending", processing: "Processing…", ready: "Ready", failed: "Failed" };
    const classes = { pending: "bg-secondary", processing: "bg-warning text-dark", ready: "bg-success", failed: "bg-danger" };

    badge.textContent = labels[status] || status;
    badge.className = `badge ${classes[status] || "bg-secondary"}`;
}

// ===== Shared: reveal + button state on any generation completing =====
// Handles BOTH cases correctly: generation that goes through a visible
// "processing" phase (via polling), AND generation that finishes so
// fast the very first response already says "ready"/"failed" — the
// bug we hit was this second, faster path never updating the UI.

function handleGenerationComplete(status, btn, linkId) {
    if (btn) {
        btn.disabled = false;
        if (status === "ready") btn.textContent = "Regenerate";
    }
    if (status === "ready") {
        const link = document.getElementById(linkId);
        if (link) link.classList.remove("d-none");
    }
}

// ===== Summary generation (Phase 4) =====

async function generateSummary(materialId) {
    const badge = document.getElementById(`summary-status-${materialId}`);
    const btn = document.querySelector(`.generate-summary-btn[data-material-id="${materialId}"]`);
    if (!badge) return;

    if (btn) btn.disabled = true;
    updateSummaryBadge(badge, "processing");

    try {
        const response = await fetch(`/summaries/${materialId}/generate`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content },
        });
        const data = await response.json();

        if (data.error) {
            updateSummaryBadge(badge, "failed");
            if (btn) btn.disabled = false;
            return;
        }

        updateSummaryBadge(badge, data.status);

        if (data.status === "processing") {
            pollSummaryStatus(materialId, badge, btn);
        } else {
            // Finished immediately (ready or failed) — handle it now,
            // same as pollSummaryStatus would have on completion.
            handleGenerationComplete(data.status, btn, `summary-link-${materialId}`);
        }
    } catch (err) {
        console.error("Failed to start summary generation:", err);
        updateSummaryBadge(badge, "failed");
        if (btn) btn.disabled = false;
    }
}

async function pollSummaryStatus(materialId, badge, btn) {
    const interval = setInterval(async () => {
        const response = await fetch(`/summaries/${materialId}/status`);
        const data = await response.json();
        updateSummaryBadge(badge, data.status);

        if (data.status === "ready" || data.status === "failed") {
            clearInterval(interval);
            handleGenerationComplete(data.status, btn, `summary-link-${materialId}`);
        }
    }, 2000);
}

function updateSummaryBadge(badge, status) {
    const labels = { pending: "No summary yet", processing: '<span class="spinner"></span> Generating…', ready: "Summary ready", failed: "Generation failed" };
    const classes = { pending: "bg-secondary", processing: "bg-warning text-dark", ready: "bg-success", failed: "bg-danger" };

    badge.innerHTML = labels[status] || status;
    badge.className = `badge ${classes[status] || "bg-secondary"}`;
}

// ===== Flashcard generation (Phase 7) =====

async function generateFlashcards(materialId) {
    const badge = document.getElementById(`flashcard-status-${materialId}`);
    const btn = document.querySelector(`.generate-flashcards-btn[data-material-id="${materialId}"]`);
    if (!badge) return;

    if (btn) btn.disabled = true;
    updateFlashcardBadge(badge, "processing");

    try {
        const response = await fetch(`/flashcards/${materialId}/generate`, {
            method: "POST",
            headers: { "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content },
        });
        const data = await response.json();

        if (data.error) {
            updateFlashcardBadge(badge, "failed");
            if (btn) btn.disabled = false;
            return;
        }

        updateFlashcardBadge(badge, data.status);

        if (data.status === "processing") {
            pollFlashcardStatus(materialId, badge, btn);
        } else {
            handleGenerationComplete(data.status, btn, `flashcard-link-${materialId}`);
        }
    } catch (err) {
        console.error("Failed to start flashcard generation:", err);
        updateFlashcardBadge(badge, "failed");
        if (btn) btn.disabled = false;
    }
}

function pollFlashcardStatus(materialId, badge, btn) {
    const interval = setInterval(async () => {
        const response = await fetch(`/flashcards/${materialId}/status`);
        const data = await response.json();
        updateFlashcardBadge(badge, data.status);

        if (data.status === "ready" || data.status === "failed") {
            clearInterval(interval);
            handleGenerationComplete(data.status, btn, `flashcard-link-${materialId}`);
        }
    }, 2000);
}

function updateFlashcardBadge(badge, status) {
    const labels = { pending: "No flashcards yet", processing: "Generating…", ready: "Flashcards ready", failed: "Generation failed" };
    const classes = { pending: "bg-secondary", processing: "bg-warning text-dark", ready: "bg-success", failed: "bg-danger" };

    badge.textContent = labels[status] || status;
    badge.className = `badge ${classes[status] || "bg-secondary"}`;
}

// ===== Wiring =====

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-pending-material]").forEach((el) => {
        processMaterial(el.dataset.pendingMaterial);
    });

    document.querySelectorAll("[data-processing-material]").forEach((el) => {
        const badge = document.getElementById(`status-${el.dataset.processingMaterial}`);
        pollStatus(el.dataset.processingMaterial, badge);
    });

    document.querySelectorAll(".retry-material-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            processMaterial(btn.dataset.materialId);
        });
    });

    document.querySelectorAll(".generate-summary-btn").forEach((btn) => {
        btn.addEventListener("click", () => generateSummary(btn.dataset.materialId));
    });

    document.querySelectorAll("[data-summary-processing]").forEach((el) => {
        const materialId = el.dataset.summaryProcessing;
        const badge = document.getElementById(`summary-status-${materialId}`);
        const btn = document.querySelector(`.generate-summary-btn[data-material-id="${materialId}"]`);
        if (btn) btn.disabled = true;
        pollSummaryStatus(materialId, badge, btn);
    });

    document.querySelectorAll(".generate-flashcards-btn").forEach((btn) => {
        btn.addEventListener("click", () => generateFlashcards(btn.dataset.materialId));
    });

    document.querySelectorAll("[data-flashcard-processing]").forEach((el) => {
        const materialId = el.dataset.flashcardProcessing;
        const badge = document.getElementById(`flashcard-status-${materialId}`);
        const btn = document.querySelector(`.generate-flashcards-btn[data-material-id="${materialId}"]`);
        if (btn) btn.disabled = true;
        pollFlashcardStatus(materialId, badge, btn);
    });
});