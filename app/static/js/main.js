document.addEventListener("DOMContentLoaded", function() {
    // Element references
    const fileInput = document.getElementById("file-upload");
    const textArea = document.getElementById("input-text");
    const form = document.getElementById("anonymise-form");
    const clearBtn = document.getElementById("clear-text");
    const outputSection = document.getElementById("output-section");
    const anonymisedText = document.getElementById("output-text");
    const anonymiseBtn = document.getElementById("anonymise-btn");
    const levelSelect = document.getElementById("level-select");
    const modelSelect = document.getElementById("model-select");

    // Spinner overlay
    function showSpinner(show) {
        let overlay = document.getElementById("overlay-spinner");
        if (overlay) overlay.style.display = show ? "flex" : "none";
    }

    // Toast notification
    function showToast(msg, style = "primary") {
        let toast = document.getElementById("main-toast");
        let toastMsg = document.getElementById("toast-message");
        if (toast && toastMsg) {
            toast.className = `toast align-items-center text-bg-${style} border-0`;
            toastMsg.innerText = msg;
            let bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }

    // Show/hide guest alert
    function showGuestAlert(show) {
        let guestAlert = document.getElementById("guest-save-alert");
        if (guestAlert) guestAlert.style.display = show ? "block" : "none";
    }

    // Show/hide Save Report button and section
    function showSaveButton(show, anonymised_text = "", input_text = "") {
        let saveActions = document.getElementById("save-actions");
        if (show) {
            if (!saveActions) {
                // Create save-actions section if it doesn't exist
                saveActions = document.createElement("div");
                saveActions.className = "text-center mt-3";
                saveActions.id = "save-actions";
                saveActions.innerHTML = `<button id="save-report-btn" class="btn btn-success px-4 mb-2">
                        <span class="material-icons align-middle">save</span> Save this report
                    </button>
                    <div id="save-report-message" class="small text-muted mt-1"></div>`;
                outputSection.appendChild(saveActions);
            } else {
                saveActions.style.display = "block";
            }
            // Store current anonymised and input text for saving
            let btn = document.getElementById("save-report-btn");
            if (btn) {
                btn.setAttribute("data-anonymised", anonymised_text);
                btn.setAttribute("data-input", input_text);
                btn.disabled = false;
                btn.style.display = "";
            }
        } else {
            if (saveActions) saveActions.style.display = "none";
        }
    }

    // Show download links after save
    function showDownloadLinks(history_id) {
        let downloadDiv = document.getElementById("download-links");
        if (downloadDiv && history_id) {
            downloadDiv.innerHTML = `
                <div class="mt-3">
                    <a href="/download/${history_id}/pdf" class="btn btn-outline-dark btn-sm mx-1" download>
                        <span class="material-icons align-middle">picture_as_pdf</span> PDF
                    </a>
                    <a href="/download/${history_id}/docx" class="btn btn-outline-primary btn-sm mx-1" download>
                        <span class="material-icons align-middle">description</span> DOCX
                    </a>
                    <a href="/download/${history_id}/txt" class="btn btn-outline-secondary btn-sm mx-1" download>
                        <span class="material-icons align-middle">text_snippet</span> TXT
                    </a>
                </div>
            `;
        }
    }

    // File upload: AJAX extract
    if (fileInput) {
        fileInput.addEventListener("change", function() {
            if (fileInput.files.length > 0) {
                let formData = new FormData();
                formData.append('file', fileInput.files[0]);
                fetch('/extract', {
                    method: 'POST',
                    body: formData
                })
                .then(r => r.json())
                .then(data => {
                    if (data.text) {
                        textArea.value = data.text;
                    }
                });
            }
        });
    }

    // Clear text & output
    if (clearBtn) {
        clearBtn.addEventListener("click", function(e) {
            e.preventDefault();
            if (textArea) textArea.value = "";
            if (anonymisedText) anonymisedText.textContent = "";
            if (outputSection) outputSection.style.display = "none";
            if (fileInput) fileInput.value = "";
            showGuestAlert(false);
            showSaveButton(false);
            let downloadDiv = document.getElementById("download-links");
            if (downloadDiv) downloadDiv.innerHTML = "";
        });
    }

    // Anonymise AJAX
    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            anonymiseBtn.disabled = true;
            anonymiseBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Anonymising...';
            showSpinner(true);

            let formData = new FormData(form);
            fetch("/", {
                method: "POST",
                body: formData,
                headers: {"X-Requested-With": "XMLHttpRequest"}
            })
            .then(r => r.json())
            .then(data => {
                showSpinner(false);
                anonymiseBtn.disabled = false;
                anonymiseBtn.innerHTML = '<span class="material-icons align-middle">auto_fix_high</span> Anonymise';

                anonymisedText.textContent = data.anonymised_text || "No output.";
                outputSection.style.display = "block";
                let downloadDiv = document.getElementById("download-links");
                if (downloadDiv) downloadDiv.innerHTML = "";
                showSaveButton(false);

                // Only show "Save" if allowed and not a guest
                if (data.can_save && !data.is_guest && data.anonymised_text && !data.anonymised_text.startsWith("Error")) {
                    showSaveButton(true, data.anonymised_text, data.input_text || "");
                } else {
                    showSaveButton(false);
                }
                // Guest logic for spaCy
                if (data.anonymised_text && data.model_used === "spacy" && data.is_guest) {
                    showGuestAlert(true);
                } else {
                    showGuestAlert(false);
                }
                setTimeout(() => outputSection.scrollIntoView({behavior: "smooth"}), 120);
            })
            .catch(() => {
                showSpinner(false);
                anonymiseBtn.disabled = false;
                anonymiseBtn.innerHTML = '<span class="material-icons align-middle">auto_fix_high</span> Anonymise';
                showToast("Anonymisation failed.", "danger");
            });
        });
    }

    // Save Report AJAX (delegated for dynamic button)
    document.addEventListener("click", function(e) {
        if (e.target && e.target.id === "save-report-btn") {
            e.preventDefault();
            // Prevent guests from saving (uses global variable set in template)
            if (typeof window.is_guest_user !== "undefined" && window.is_guest_user) {
                showToast("Please log in to save reports.", "warning");
                return;
            }
            let btn = e.target;
            btn.disabled = true;
            showSpinner(true);
            let anonymised = btn.getAttribute("data-anonymised");
            let input = btn.getAttribute("data-input");
            fetch("/save-report", {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                body: new URLSearchParams({
                    anonymised_text: anonymised,
                    input_text: input,
                    level: levelSelect.value,
                    model_used: modelSelect.value,
                    filename: fileInput && fileInput.files[0] ? fileInput.files[0].name : ""
                })
            })
            .then(res => res.json())
            .then(data => {
                showSpinner(false);
                let msgDiv = document.getElementById("save-report-message");
                if (data.success) {
                    showToast("Report saved!", "success");
                    showDownloadLinks(data.history_id);
                    btn.style.display = "none";
                    if (msgDiv) {
                        msgDiv.innerText = "Report saved! You can download it below or find it in your dashboard.";
                        msgDiv.className = "text-success mt-1";
                    }
                } else {
                    showToast(data.msg || "Failed to save report.", "danger");
                    btn.disabled = false;
                    if (msgDiv) {
                        msgDiv.innerText = "Failed to save report. Try again.";
                        msgDiv.className = "text-danger mt-1";
                    }
                }
            })
            .catch(() => {
                showSpinner(false);
                showToast("Error saving report.", "danger");
                btn.disabled = false;
            });
        }
    });

    // Defensive: If Save should be visible on page load (e.g. SSR with can_save)
    if (typeof window.is_guest_user !== "undefined" && !window.is_guest_user) {
        let saveActions = document.getElementById("save-actions");
        if (saveActions) saveActions.style.display = "block";
    }
});
