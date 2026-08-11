/*

* Learnio - Global UI JavaScript
  */

document.addEventListener("DOMContentLoaded", function () {

/*
 * Mobile sidebar
 */
const sidebarToggle = document.getElementById("sidebar-toggle");
const sidebar = document.querySelector(".sidebar");

if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
        sidebar.classList.toggle("active");
    });
}


/*
 * Close mobile sidebar when clicking outside it
 */
document.addEventListener("click", function (event) {

    if (!sidebar || !sidebarToggle) {
        return;
    }

    if (
        sidebar.classList.contains("active") &&
        !sidebar.contains(event.target) &&
        !sidebarToggle.contains(event.target)
    ) {
        sidebar.classList.remove("active");
    }

});


/*
 * Auto-dismiss flash alerts
 */
const alerts = document.querySelectorAll(".alert");

alerts.forEach(function (alert) {

    setTimeout(function () {

        alert.style.transition =
            "opacity 0.35s ease, transform 0.35s ease";

        alert.style.opacity = "0";
        alert.style.transform = "translateY(-5px)";

        setTimeout(function () {
            alert.remove();
        }, 350);

    }, 5000);

});


/*
 * Prevent accidental double submission
 * for normal forms.
 */
document.querySelectorAll("form").forEach(function (form) {

    form.addEventListener("submit", function () {

        if (form.dataset.submitting === "true") {
            return;
        }

        form.dataset.submitting = "true";

        const submitButtons =
            form.querySelectorAll(
                'button[type="submit"], input[type="submit"]'
            );

        submitButtons.forEach(function (button) {

            button.disabled = true;

            const originalText =
                button.dataset.originalText ||
                button.innerHTML;

            button.dataset.originalText = originalText;

            if (button.tagName === "BUTTON") {
                button.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }

        });

    });

});


/*
 * Add a small visual interaction to buttons.
 */
document.querySelectorAll(".btn").forEach(function (button) {

    button.addEventListener("mousedown", function () {
        this.style.transform = "translateY(1px)";
    });

    button.addEventListener("mouseup", function () {
        this.style.transform = "";
    });

    button.addEventListener("mouseleave", function () {
        this.style.transform = "";
    });

});


/*
 * Confirm destructive actions.
 *
 * Only activates for forms explicitly marked:
 *
 * data-confirm="..."
 */
document.querySelectorAll("form[data-confirm]").forEach(function (form) {

    form.addEventListener("submit", function (event) {

        const message =
            form.dataset.confirm ||
            "Are you sure you want to continue?";

        if (!window.confirm(message)) {
            event.preventDefault();
        }

    });

});


/*
 * Automatically focus the first visible form field.
 *
 * This avoids moving focus on pages where the user is
 * already interacting with another element.
 */
const firstInput = document.querySelector(
    "form input:not([type='hidden']):not([disabled]), " +
    "form textarea:not([disabled]), " +
    "form select:not([disabled])"
);

if (
    firstInput &&
    window.innerWidth > 700 &&
    !document.activeElement ||
    document.activeElement === document.body
) {
    firstInput.focus();
}


/*
 * Global keyboard shortcut:
 * Escape closes the mobile sidebar.
 */
document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {

        if (sidebar) {
            sidebar.classList.remove("active");
        }

    }

});

});
