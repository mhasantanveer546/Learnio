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
        }
    }, 2000);
}

function updateBadge(badge, status) {
    const labels = { pending: "Pending", processing: "Processing…", ready: "Ready", failed: "Failed" };
    const classes = { pending: "bg-secondary", processing: "bg-warning text-dark", ready: "bg-success", failed: "bg-danger" };

    badge.textContent = labels[status] || status;
    badge.className = `badge ${classes[status] || "bg-secondary"}`;
}

document.addEventListener("DOMContentLoaded", () => {
    // pending materials: trigger processing for the first time
    document.querySelectorAll("[data-pending-material]").forEach((el) => {
        processMaterial(el.dataset.pendingMaterial);
    });

    // processing materials (e.g. page was refreshed mid-extraction):
    // only poll, never re-trigger extraction
    document.querySelectorAll("[data-processing-material]").forEach((el) => {
        const badge = document.getElementById(`status-${el.dataset.processingMaterial}`);
        pollStatus(el.dataset.processingMaterial, badge);
    });

    // failed materials: manual retry button
    document.querySelectorAll(".retry-material-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            processMaterial(btn.dataset.materialId);
        });
    });
});