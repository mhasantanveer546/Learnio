// ===== Flashcard study view (Phase 7) =====

document.addEventListener("DOMContentLoaded", () => {
    const dataEl = document.getElementById("flashcard-data");
    if (!dataEl) return; // not on the study page

    const { cards } = JSON.parse(dataEl.textContent);
    if (cards.length === 0) return;

    let index = 0;
    let flipped = false;

    const scene = document.getElementById("flashcard-scene");
    const flashcard = document.getElementById("flashcard");
    const frontText = document.getElementById("card-front-text");
    const backText = document.getElementById("card-back-text");
    const positionLabel = document.getElementById("card-position");
    const learnedCountLabel = document.getElementById("learned-count");
    const progressBar = document.getElementById("progress-bar");
    const learnedCheckbox = document.getElementById("mark-learned");
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    function renderCard() {
        const card = cards[index];
        frontText.textContent = card.front;
        backText.textContent = card.back;
        flipped = false;
        flashcard.classList.remove("is-flipped");
        learnedCheckbox.checked = card.is_learned;
        positionLabel.textContent = `Card ${index + 1} of ${cards.length}`;
        updateRatingButtons(card.difficulty);
    }

    function updateRatingButtons(activeDifficulty) {
        const map = { hard: "rate-hard", medium: "rate-medium", easy: "rate-easy" };
        Object.values(map).forEach(id => document.getElementById(id).classList.remove("active"));
        if (map[activeDifficulty]) {
            document.getElementById(map[activeDifficulty]).classList.add("active");
        }
    }

    function updateProgress() {
        const learned = cards.filter(c => c.is_learned).length;
        learnedCountLabel.textContent = `${learned} learned`;
        progressBar.style.width = `${(learned / cards.length) * 100}%`;
    }

    async function markCard(payload) {
        const card = cards[index];
        try {
            const response = await fetch(`/flashcards/card/${card.id}/mark`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (data.error) return;

            card.is_learned = data.is_learned;
            card.difficulty = data.difficulty;
            updateProgress();
            updateRatingButtons(card.difficulty);
        } catch (err) {
            console.error("Failed to update card:", err);
        }
    }

    flashcard.addEventListener("click", () => {
        flipped = !flipped;
        flashcard.classList.toggle("is-flipped", flipped);
    });

    document.getElementById("prev-card").addEventListener("click", () => {
        index = (index - 1 + cards.length) % cards.length;
        renderCard();
    });

    document.getElementById("next-card").addEventListener("click", () => {
        index = (index + 1) % cards.length;
        renderCard();
    });

    document.getElementById("rate-hard").addEventListener("click", () => markCard({ difficulty: "hard" }));
    document.getElementById("rate-medium").addEventListener("click", () => markCard({ difficulty: "medium" }));
    document.getElementById("rate-easy").addEventListener("click", () => markCard({ difficulty: "easy" }));

    learnedCheckbox.addEventListener("change", (e) => markCard({ is_learned: e.target.checked }));

    renderCard();
    updateProgress();
});