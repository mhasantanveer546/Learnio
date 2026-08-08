async function fetchJSON(url) {
    const response = await fetch(url);
    return response.json();
}

async function renderAnalyticsCharts() {
    // Study Hours — stacked bar, subject vs general time
    const hoursEl = document.getElementById("chart-study-hours");
    if (hoursEl) {
        const data = await fetchJSON("/analytics/data/study-hours");
        new Chart(hoursEl, {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [
                    { label: "Subject Study", data: data.subject_minutes.map(m => (m / 60).toFixed(1)), backgroundColor: "#2563EB" },
                    { label: "General Study", data: data.general_minutes.map(m => (m / 60).toFixed(1)), backgroundColor: "#94A3B8" },
                ],
            },
            options: { scales: { x: { stacked: true }, y: { stacked: true, title: { display: true, text: "Hours" } } } },
        });
    }

    // Quiz Scores — line chart
    const quizEl = document.getElementById("chart-quiz-scores");
    if (quizEl) {
        const data = await fetchJSON("/analytics/data/quiz-scores");
        new Chart(quizEl, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{ label: "Score %", data: data.scores, borderColor: "#7C3AED", tension: 0.3, fill: false }],
            },
            options: { scales: { y: { min: 0, max: 100 } } },
        });
    }

    // Uploads — bar chart
    const uploadsEl = document.getElementById("chart-uploads");
    if (uploadsEl) {
        const data = await fetchJSON("/analytics/data/uploads");
        new Chart(uploadsEl, {
            type: "bar",
            data: { labels: data.labels, datasets: [{ label: "Uploads", data: data.counts, backgroundColor: "#10B981" }] },
            options: { scales: { y: { ticks: { stepSize: 1 } } } },
        });
    }

    // Subject distribution — doughnut
    const subjectsEl = document.getElementById("chart-subjects");
    if (subjectsEl) {
        const data = await fetchJSON("/analytics/data/subjects");
        if (data.labels.length === 0) {
            subjectsEl.parentElement.innerHTML += '<p class="text-muted small mt-2">No subject-scoped study time logged yet.</p>';
        } else {
            new Chart(subjectsEl, {
                type: "doughnut",
                data: { labels: data.labels, datasets: [{ data: data.minutes, backgroundColor: data.colors }] },
            });
        }
    }
}