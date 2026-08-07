document.addEventListener("DOMContentLoaded", () => {
    setupQuizNavigation();
    setupQuizTimer();
    setupSelfGrading();
});

function setupQuizNavigation() {
    const questions = document.querySelectorAll(".quiz-question");
    if (questions.length === 0) return;

    let current = 0;
    const prevBtn = document.getElementById("quiz-prev");
    const nextBtn = document.getElementById("quiz-next");
    const submitBtn = document.getElementById("quiz-submit");
    const progressBar = document.getElementById("quiz-progress");

    function show(index) {
        questions.forEach((q, i) => q.style.display = i === index ? "block" : "none");
        prevBtn.disabled = index === 0;
        nextBtn.style.display = index === questions.length - 1 ? "none" : "inline-block";
        submitBtn.style.display = index === questions.length - 1 ? "inline-block" : "none";
        progressBar.style.width = `${((index + 1) / questions.length) * 100}%`;
    }

    prevBtn.addEventListener("click", () => { if (current > 0) show(--current); });
    nextBtn.addEventListener("click", () => { if (current < questions.length - 1) show(++current); });

    show(0);
}

function setupQuizTimer() {
    const timerEl = document.getElementById("quiz-timer");
    if (!timerEl || typeof QUIZ_TIME_LIMIT_SECONDS === "undefined") return;

    let remaining = QUIZ_TIME_LIMIT_SECONDS;

    const interval = setInterval(() => {
        remaining--;
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        timerEl.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;

        if (remaining <= 60) timerEl.classList.add("text-danger");

        if (remaining <= 0) {
            clearInterval(interval);
            document.getElementById("quiz-form").submit(); // auto-submit on timeout
        }
    }, 1000);
}

function setupSelfGrading() {
    document.querySelectorAll(".self-grade-group").forEach((group) => {
        const answerId = group.dataset.answerId;

        group.querySelectorAll(".grade-btn").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const isCorrect = btn.dataset.correct === "true";

                try {
                    const response = await fetch(`/quizzes/answer/${answerId}/self-grade`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
                        },
                        body: JSON.stringify({ is_correct: isCorrect }),
                    });
                    const data = await response.json();

                    group.outerHTML = isCorrect
                        ? '<span class="badge bg-success">Marked correct</span>'
                        : '<span class="badge bg-danger">Marked incorrect</span>';

                    // Reflect the updated running score at the top of the page, if present
                    const scoreHeading = document.querySelector(".card h3");
                    if (scoreHeading) scoreHeading.textContent = `${data.score} / ${data.total}`;
                } catch (err) {
                    console.error("Self-grading failed:", err);
                }
            });
        });
    });
}