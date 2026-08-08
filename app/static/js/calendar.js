document.addEventListener("DOMContentLoaded", () => {
    const calendarEl = document.getElementById("calendar");
    if (!calendarEl) return;

    const modalEl = document.getElementById("eventModal");
    const modal = new bootstrap.Modal(modalEl);

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        headerToolbar: { left: "prev,next today", center: "title", right: "" },
        height: "auto",
        events: "/calendar/events",
        eventClick: function (info) {
            const props = info.event.extendedProps;

            document.getElementById("eventModalTitle").textContent = info.event.title;

            let body = `<p class="mb-1"><strong>Subject:</strong> ${props.subject}</p>`;
            body += `<p class="mb-1"><strong>Date:</strong> ${info.event.start.toLocaleString()}</p>`;
            if (props.type === "assignment") {
                body += `<p class="mb-1"><strong>Priority:</strong> ${props.priority}</p>`;
                body += `<p class="mb-1"><strong>Status:</strong> ${props.status}</p>`;
            } else if (props.location) {
                body += `<p class="mb-1"><strong>Location:</strong> ${props.location}</p>`;
            }
            document.getElementById("eventModalBody").innerHTML = body;
            document.getElementById("eventModalEditLink").href = props.editUrl;

            modal.show();
        },
    });

    calendar.render();
});