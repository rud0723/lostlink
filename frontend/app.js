const API_URL = "http://127.0.0.1:8000";

const reportForm = document.getElementById("reportForm");
const message = document.getElementById("message");

reportForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    message.textContent = "Submitting report...";

    const formData = new FormData(reportForm);

    try {

        const response = await fetch(`${API_URL}/report`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (response.ok) {

            message.textContent =
                `Report submitted successfully! Report ID: ${result.report_id}`;

            reportForm.reset();

        } else {

            console.error("Server error:", result);

            message.textContent =
                `Error: ${result.detail || "Could not submit report."}`;
        }

    } catch (error) {

        console.error("Connection error:", error);

        message.textContent =
            "Could not connect to LostLink server.";
    }

});