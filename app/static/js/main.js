// Global JS entry point. Page-specific behavior (quiz timers, flashcard
// flips, chart rendering, etc.) will live in their own files and load
// via {% block extra_js %} rather than being crammed in here.

document.addEventListener("DOMContentLoaded", () => {
    console.log("Learnio loaded");
});