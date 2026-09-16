"use strict";

const API_URL = window.location.origin;


/* =====================================================
   HELPER FUNCTIONS
===================================================== */

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function setMessage(elementId, message, success = true) {

    const element = document.getElementById(elementId);

    if (!element) {
        return;
    }

    element.textContent = message;

    element.style.color = success
        ? "#166534"
        : "#dc2626";
}


async function requestJSON(url, options = {}) {

    const response = await fetch(url, options);

    const text = await response.text();

    let data;

    try {
        data = JSON.parse(text);
    } catch {
        throw new Error(
            "Server returned an invalid response."
        );
    }

    if (!response.ok) {

        throw new Error(
            data.detail ||
            data.message ||
            "Server error: " + response.status
        );

    }

    return data;
}


/* =====================================================
   NAVIGATION
===================================================== */

function openSection(sectionId) {

    document
        .querySelectorAll(".section")
        .forEach(function(section) {

            section.classList.remove("active");

        });


    document
        .querySelectorAll(".nav-button")
        .forEach(function(button) {

            button.classList.remove("active");

        });


    const section =
        document.getElementById(sectionId);


    const button =
        document.getElementById(
            "nav-" + sectionId
        );


    if (section) {

        section.classList.add("active");

    }


    if (button) {

        button.classList.add("active");

    }


    if (sectionId === "dashboard") {

        loadDashboard();

    }


    if (sectionId === "registered") {

        loadItems();

    }


    if (sectionId === "reports") {

        loadReports();

    }

}


/* =====================================================
   DASHBOARD
===================================================== */

async function loadDashboard() {

    try {

        const items =
            await requestJSON(
                API_URL + "/registered-items-data"
            );


        const reports =
            await requestJSON(
                API_URL + "/reports"
            );


        const totalItems =
            items.length;


        const totalLost =
            reports.filter(function(report) {

                return report.report_type === "LOST";

            }).length;


        const totalFound =
            reports.filter(function(report) {

                return report.report_type === "FOUND";

            }).length;


        const totalNotified =
            items.filter(function(item) {

                return item.status === "NOTIFIED";

            }).length;


        document.getElementById(
            "total-items"
        ).textContent = totalItems;


        document.getElementById(
            "total-lost"
        ).textContent = totalLost;


        document.getElementById(
            "total-found"
        ).textContent = totalFound;


        document.getElementById(
            "total-notified"
        ).textContent = totalNotified;

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }

}


/* =====================================================
   REGISTERED ITEMS
===================================================== */

async function loadItems() {

    const tableBody =
        document.getElementById(
            "items-table-body"
        );


    if (!tableBody) {
        return;
    }


    tableBody.innerHTML =
        '<tr><td colspan="7">Loading...</td></tr>';


    try {

        const items =
            await requestJSON(
                API_URL + "/registered-items-data"
            );


        if (!items.length) {

            tableBody.innerHTML =
                '<tr><td colspan="7" class="empty">No registered items.</td></tr>';

            return;
        }


        tableBody.innerHTML =
            items.map(function(item) {

                return `
                    <tr>

                        <td>
                            ${escapeHTML(item.id)}
                        </td>

                        <td>
                            <strong>
                                ${escapeHTML(item.code)}
                            </strong>
                        </td>

                        <td>
                            ${escapeHTML(item.name)}
                        </td>

                        <td>
                            ${escapeHTML(item.category)}
                        </td>

                        <td>
                            ${escapeHTML(item.color)}
                        </td>

                        <td>
                            ${escapeHTML(item.brand)}
                        </td>

                        <td>
                            <span class="status">
                                ${escapeHTML(item.status)}
                            </span>
                        </td>

                    </tr>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "Items error:",
            error
        );


        tableBody.innerHTML =
            `<tr>
                <td colspan="7">
                    Error loading items:
                    ${escapeHTML(error.message)}
                </td>
            </tr>`;

    }

}


/* =====================================================
   REGISTER ITEM
===================================================== */

async function registerItem(event) {

    event.preventDefault();


    const form =
        document.getElementById(
            "registerForm"
        );


    const message =
        document.getElementById(
            "register-message"
        );


    const qrResult =
        document.getElementById(
            "qr-result"
        );


    message.textContent =
        "Registering item...";


    message.style.color =
        "#2563eb";


    qrResult.style.display =
        "none";


    try {

        const formData =
            new FormData(form);


        const data =
            await requestJSON(
                API_URL + "/register-item",
                {
                    method: "POST",
                    body: formData
                }
            );


        if (data.status !== "success") {

            throw new Error(
                data.message ||
                "Registration failed."
            );

        }


        message.textContent =
            data.message ||
            "Item registered successfully.";


        message.style.color =
            "#166534";


        document.getElementById(
            "generated-code"
        ).textContent =
            data.code;


        const qrImage =
            document.getElementById(
                "generated-qr"
            );


        qrImage.src =
            data.qr_url;


        const generatedLink =
            document.getElementById(
                "generated-link"
            );


        const itemURL =
            API_URL +
            "/item/" +
            encodeURIComponent(data.code);


        generatedLink.href =
            itemURL;


        generatedLink.textContent =
            itemURL;


        qrResult.style.display =
            "block";


        form.reset();


        loadDashboard();

    } catch (error) {

        console.error(
            "Register item error:",
            error
        );


        message.textContent =
            "Error: " +
            error.message;


        message.style.color =
            "#dc2626";

    }

}


/* =====================================================
   REPORT
===================================================== */

async function submitReport(event) {

    event.preventDefault();


    const form =
        document.getElementById(
            "reportForm"
        );


    setMessage(
        "report-message",
        "Submitting report...",
        true
    );


    try {

        const formData =
            new FormData(form);


        /*
         * Empty latitude/longitude values can cause
         * FastAPI form conversion problems.
         */
        const latitude =
            formData.get("latitude");


        const longitude =
            formData.get("longitude");


        if (
            latitude === null ||
            latitude === ""
        ) {

            formData.delete("latitude");

        }


        if (
            longitude === null ||
            longitude === ""
        ) {

            formData.delete("longitude");

        }


        const data =
            await requestJSON(
                API_URL + "/report",
                {
                    method: "POST",
                    body: formData
                }
            );


        if (data.status !== "success") {

            throw new Error(
                data.message ||
                "Report submission failed."
            );

        }


        setMessage(
            "report-message",
            "Report submitted successfully. Report ID: " +
            data.report_id,
            true
        );


        form.reset();


        setCurrentDateTime();


        loadReports();

        loadDashboard();

    } catch (error) {

        console.error(
            "Report error:",
            error
        );


        setMessage(
            "report-message",
            "Error: " + error.message,
            false
        );

    }

}


/* =====================================================
   LOAD REPORTS
===================================================== */

async function loadReports() {

    const container =
        document.getElementById(
            "reports-list"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        '<div class="empty">Loading reports...</div>';


    try {

        const reports =
            await requestJSON(
                API_URL + "/reports"
            );


        if (!reports.length) {

            container.innerHTML =
                '<div class="empty">No reports yet.</div>';

            return;
        }


        container.innerHTML =
            reports.map(function(report) {

                return `
                    <div class="report-card">

                        <h3>
                            ${escapeHTML(report.report_type)}
                            Report #${escapeHTML(report.id)}
                        </h3>

                        <p>
                            <strong>Category:</strong>
                            ${escapeHTML(report.category)}
                        </p>

                        <p>
                            <strong>Color:</strong>
                            ${escapeHTML(report.color)}
                        </p>

                        <p>
                            <strong>Brand:</strong>
                            ${escapeHTML(report.brand)}
                        </p>

                        <p>
                            <strong>Location:</strong>
                            ${escapeHTML(report.location)}
                        </p>

                        <p>
                            <strong>Date & Time:</strong>
                            ${escapeHTML(report.date_time)}
                        </p>

                        <p>
                            <strong>Description:</strong>
                            ${escapeHTML(report.description)}
                        </p>

                    </div>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "Reports error:",
            error
        );


        container.innerHTML =
            `<div class="empty">
                Error loading reports:
                ${escapeHTML(error.message)}
            </div>`;

    }

}


/* =====================================================
   FIND MATCHES
===================================================== */

async function findMatches() {

    const input =
        document.getElementById(
            "match-report-id"
        );


    const container =
        document.getElementById(
            "matches-list"
        );


    const reportId =
        input.value.trim();


    if (!reportId) {

        setMessage(
            "match-message",
            "Please enter a LOST report ID.",
            false
        );

        return;

    }


    setMessage(
        "match-message",
        "Finding matches...",
        true
    );


    container.innerHTML =
        '<div class="empty">Searching...</div>';


    try {

        const data =
            await requestJSON(
                API_URL +
                "/matches/" +
                encodeURIComponent(reportId)
            );


        if (data.status !== "success") {

            throw new Error(
                data.message ||
                "Could not find matches."
            );

        }


        const matches =
            data.matches || [];


        if (!matches.length) {

            container.innerHTML =
                '<div class="empty">No matching found reports.</div>';

            setMessage(
                "match-message",
                "Search completed.",
                true
            );

            return;

        }


        container.innerHTML =
            matches.map(function(match) {

                const report =
                    match.report ||
                    match;


                return `
                    <div class="match-card">

                        <h3>
                            Possible Match
                        </h3>

                        <p>
                            <strong>Report ID:</strong>
                            ${escapeHTML(report.id)}
                        </p>

                        <p>
                            <strong>Category:</strong>
                            ${escapeHTML(report.category)}
                        </p>

                        <p>
                            <strong>Color:</strong>
                            ${escapeHTML(report.color)}
                        </p>

                        <p>
                            <strong>Brand:</strong>
                            ${escapeHTML(report.brand)}
                        </p>

                        <p>
                            <strong>Location:</strong>
                            ${escapeHTML(report.location)}
                        </p>

                    </div>
                `;

            }).join("");


        setMessage(
            "match-message",
            "Matches found.",
            true
        );

    } catch (error) {

        console.error(
            "Match error:",
            error
        );


        container.innerHTML =
            `<div class="empty">
                Error:
                ${escapeHTML(error.message)}
            </div>`;


        setMessage(
            "match-message",
            "Could not find matches.",
            false
        );

    }

}


/* =====================================================
   DATE & TIME
===================================================== */

function setCurrentDateTime() {

    const input =
        document.getElementById(
            "date-time"
        );


    if (!input) {
        return;
    }


    const now =
        new Date();


    const local =
        new Date(
            now.getTime() -
            now.getTimezoneOffset() * 60000
        );


    input.value =
        local
            .toISOString()
            .slice(0, 16);

}


/* =====================================================
   INITIALIZE
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        /* Navigation */

        document
            .getElementById("nav-dashboard")
            .addEventListener(
                "click",
                function() {
                    openSection("dashboard");
                }
            );


        document
            .getElementById("nav-register")
            .addEventListener(
                "click",
                function() {
                    openSection("register");
                }
            );


        document
            .getElementById("nav-registered")
            .addEventListener(
                "click",
                function() {
                    openSection("registered");
                }
            );


        document
            .getElementById("nav-reports")
            .addEventListener(
                "click",
                function() {
                    openSection("reports");
                }
            );


        document
            .getElementById("nav-matches")
            .addEventListener(
                "click",
                function() {
                    openSection("matches");
                }
            );


        /* Register form */

        document
            .getElementById("registerForm")
            .addEventListener(
                "submit",
                registerItem
            );


        /* Report form */

        document
            .getElementById("reportForm")
            .addEventListener(
                "submit",
                submitReport
            );


        /* Match button */

        document
            .getElementById("find-match-button")
            .addEventListener(
                "click",
                findMatches
            );


        /* Initial data */

        setCurrentDateTime();

        loadDashboard();

    }
);