document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("global-search-input");
    const dropdown = document.getElementById("search-live-results");
    if (!input || !dropdown) return;

    let debounceTimer;

    // Maps each result type to how its URL is built from url_kwargs.
    // Mirrors the same routing decisions made in results.html — kept
    // in one place here so it's easy to update if routes ever change.
    const urlBuilders = {
        subjects: (kwargs) => `/subjects/${kwargs.subject_id}`,
        materials: (kwargs) => `/subjects/${kwargs.subject_id}`,
        summaries: (kwargs) => `/summaries/${kwargs.material_id}`,
        flashcards: (kwargs) => `/flashcards/${kwargs.material_id}`,
        assignments: () => `/assignments/`,
        exams: () => `/exams/`,
    };

    input.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();

        if (query.length < 2) {
            dropdown.classList.add("d-none");
            return;
        }

        debounceTimer = setTimeout(() => fetchLiveResults(query), 300);
    });

    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target) && e.target !== input) {
            dropdown.classList.add("d-none");
        }
    });

    async function fetchLiveResults(query) {
        try {
            const response = await fetch(`/search/live?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            renderDropdown(data);
        } catch (err) {
            console.error("Live search failed:", err);
        }
    }

    function renderDropdown(data) {
        const groups = Object.entries(data).filter(([, items]) => items.length > 0);

        if (groups.length === 0) {
            dropdown.innerHTML = `<div class="p-3 text-muted small">No quick results — press Enter to search fully.</div>`;
        } else {
            dropdown.innerHTML = groups.map(([type, items]) => `
                <div class="px-3 pt-2 pb-1 text-uppercase text-muted small fw-semibold">${type}</div>
                ${items.map(item => {
                    const builder = urlBuilders[type];
                    const href = builder ? builder(item.url_kwargs) : "#";
                    return `
                        <a href="${href}" class="d-block px-3 py-2 border-top small text-decoration-none text-dark">
                            <div class="fw-semibold">${escapeHtml(item.title)}</div>
                            ${item.subtitle ? `<div class="text-muted">${escapeHtml(item.subtitle)}</div>` : ""}
                        </a>
                    `;
                }).join("")}
            `).join("");
        }

        dropdown.classList.remove("d-none");
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
});