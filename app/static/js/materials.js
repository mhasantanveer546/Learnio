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

            // The summary controls block was rendered hidden at page-load
            // time (material wasn't ready yet) — reveal it now instead of
            // requiring a manual refresh.
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
        } else if (btn) {
            btn.disabled = false;
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
            if (btn) {
                btn.disabled = false;
                if (data.status === "ready") {
                    btn.textContent = "Regenerate";
                }
            }
            if (data.status === "ready") {
                const link = document.getElementById(`summary-link-${materialId}`);
                if (link) link.classList.remove("d-none");
            }
        }
    }, 2000);
}

function updateSummaryBadge(badge, status) {
    const labels = { pending: "No summary yet", processing: "Generating…", ready: "Summary ready", failed: "Generation failed" };
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
        btn.addEventListener("click", () => {
            generateSummary(btn.dataset.materialId);
        });
    });

    document.querySelectorAll("[data-summary-processing]").forEach((el) => {
        const materialId = el.dataset.summaryProcessing;
        const badge = document.getElementById(`summary-status-${materialId}`);
        const btn = document.querySelector(`.generate-summary-btn[data-material-id="${materialId}"]`);
        if (btn) btn.disabled = true;
        pollSummaryStatus(materialId, badge, btn);
    });
});