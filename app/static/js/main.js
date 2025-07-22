document.addEventListener('DOMContentLoaded', function () {
    // --- State Management ---
    let originalText = '';
    let anonymizationSteps = [];
    let currentStepIndex = 0;
    let userChoices = [];
    let currentFinalOutput = {
        highlighted: '',
        clean: ''
    };

    const anonymizerContainer = document.querySelector('.anonymizer-container');
    if (!anonymizerContainer) return;

    // --- Element Selectors ---
    const originalTextInput = document.getElementById('original-text');
    const fileUpload = document.getElementById('file-upload');
    const fileNameSpan = document.getElementById('file-name');
    const clearTextBtn = document.getElementById('clear-text-btn');
    const modelSelect = document.getElementById('model-select');
    const levelSelect = document.getElementById('level-select');
    const startBtn = document.getElementById('start-btn');
    const spacyStepper = document.getElementById('spacy-stepper');
    const stepperContent = document.getElementById('stepper-content');
    const progressText = document.getElementById('progress-text');
    const progressBar = document.getElementById('progress-bar');
    const prevStepBtn = document.getElementById('prev-step-btn');
    const nextStepBtn = document.getElementById('next-step-btn');
    const finalizeBtn = document.getElementById('finalize-btn');
    const loadingSpinner = document.getElementById('loading-spinner');
    const outputSection = document.getElementById('output-section');
    const anonymizedOutput = document.getElementById('anonymized-output');
    const saveReportBtn = document.getElementById('save-report-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    const downloadDocxBtn = document.getElementById('download-docx-btn');
    const downloadModal = document.getElementById('download-modal');
    const levelDescriptionBox = document.getElementById('level-description-box');

    // --- Descriptions for Anonymization Levels ---
    const levelDescriptions = {
        low: {
            title: 'Level 1: Essential Privacy',
            details: `Focuses on removing only the most direct personal identifiers. This level targets:
                <ul>
                    <li><strong>Names</strong> of people (PERSON).</li>
                    <li><strong>Ages</strong> of individuals (AGE).</li>
                </ul>`
        },
        medium: {
            title: 'Level 2: Balanced Privacy',
            details: `Removes direct personal details and indirect contextual identifiers. This is the recommended level for most reports. This level targets:
                <ul>
                    <li>Everything from Level 1, plus:</li>
                    <li><strong>Organizations</strong> (e.g., companies, agencies) (ORG).</li>
                    <li><strong>Specific Buildings</strong> (e.g., stadiums, clinics) (FAC).</li>
                    <li><strong>Specific Locations</strong> (e.g., street names) (LOC).</li>
                    <li><strong>Geopolitical Locations</strong> (e.g., cities, countries) (GPE).</li>
                </ul>`
        },
        high: {
            title: 'Level 3: Maximum Privacy',
            details: `Performs the most aggressive anonymization, removing all personal, contextual, and temporal data that could be used to identify someone. This level targets:
                <ul>
                    <li>Everything from Levels 1 and 2, plus:</li>
                    <li><strong>Dates</strong> (e.g., "July 22, 2025") (DATE).</li>
                    <li><strong>Times</strong> (e.g., "4:30 PM") (TIME).</li>
                    <li><strong>Monetary values</strong> (e.g., "£50", "$200") (MONEY).</li>
                </ul>`
        }
    };

    // --- Functions ---
    function updateLevelDescription() {
        const selectedLevel = levelSelect.value;
        const description = levelDescriptions[selectedLevel];
        if (description) {
            levelDescriptionBox.innerHTML = `<h4>${description.title}</h4><p>${description.details}</p>`;
        }
    }

    function resetUI() {
        spacyStepper.classList.add('hidden');
        outputSection.classList.add('hidden');
        loadingSpinner.classList.add('hidden');
        startBtn.disabled = false;
        // Re-add icon to button text on reset
        startBtn.innerHTML = `<span class="material-icons-outlined">play_arrow</span>Start Anonymization`;
    }

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        fileNameSpan.textContent = file.name;
        const formData = new FormData();
        formData.append('file', file);
        showLoading(true, 'Extracting text from file...');
        try {
            const response = await fetch('/upload-file', {method: 'POST', body: formData});
            const data = await response.json();
            if (response.ok) {
                originalTextInput.value = data.text;
                originalText = data.text;
            } else {
                showError(data.error || 'Failed to extract text.');
            }
        } catch (error) {
            showError('An error occurred during file upload.');
        } finally {
            showLoading(false);
        }
    }

    function handleStart() {
        originalText = originalTextInput.value;
        if (!originalText.trim()) {
            showError('Please provide text or upload a file to anonymize.');
            return;
        }
        resetUI();
        const selectedModel = modelSelect.value;
        showLoading(true, selectedModel === 'chatgpt' ? 'AI is processing your report...' : 'Analyzing text...');
        if (selectedModel === 'spacy') startSpacyProcess();
        else if (selectedModel === 'chatgpt') startGptProcess();
    }

    async function startSpacyProcess() {
        try {
            const response = await fetch('/process-text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: originalText, level: levelSelect.value})
            });
            const data = await response.json();
            showLoading(false);
            if (response.ok) {
                anonymizationSteps = data;
                if (anonymizationSteps.length === 0) {
                    showInfo("No items found to anonymize for the selected level.");
                    displayFinalResult({
                        anonymized_text_highlighted: originalText,
                        anonymized_text_clean: originalText
                    });
                    return;
                }
                userChoices = anonymizationSteps.map(step => ({
                    original_list: step.text_to_replace,
                    original: step.display_text,
                    replacement: step.display_text
                }));
                currentStepIndex = 0;
                spacyStepper.classList.remove('hidden');
                renderStep(currentStepIndex);
            } else {
                showError(data.error || 'Failed to process text.');
            }
        } catch (error) {
            showLoading(false);
            showError('An error occurred while communicating with the server.');
        }
    }

    function renderStep(index) {
        const step = anonymizationSteps[index];
        if (!step) return;
        let suggestionsHTML = step.suggestions.map(s => `<label class="suggestion-item"><input type="radio" name="replacement" value="${s}">${s}</label>`).join('');
        stepperContent.innerHTML = `
            <div class="step-content">
                <div class="step-header">
                    <h4>Reviewing entity: <span class="original-word">${step.display_text}</span></h4>
                    <p>Entity Type: ${step.label}</p>
                    ${step.label === 'PERSON' && step.text_to_replace.length > 1 ? `<p><small>This change will affect all variations, including: ${step.text_to_replace.join(', ')}</small></p>` : ''}
                </div>
                <div class="form-group">
                    <label>Choose a replacement:</label>
                    <div class="suggestion-grid">
                        ${suggestionsHTML}
                        <label class="suggestion-item custom-option"><input type="radio" name="replacement" value="custom">Use a custom replacement:<input type="text" id="custom-input" placeholder="Enter custom value"></label>
                        <label class="suggestion-item"><input type="radio" name="replacement" value="${step.display_text}" checked>Keep original: "${step.display_text}"</label>
                    </div>
                </div>
            </div>`;
        updateStepperNav();
        updateProgressBar();
        restoreStepChoice(index);
        stepperContent.querySelectorAll('input[name="replacement"]').forEach(radio => radio.addEventListener('change', handleStepChoice));
        document.getElementById('custom-input').addEventListener('input', handleStepChoice);
    }

    function handleStepChoice(e) {
        const customInput = document.getElementById('custom-input');
        const customRadio = document.querySelector('input[value="custom"]');
        let chosenValue = document.querySelector('input[name="replacement"]:checked').value;
        if (e.target.id === 'custom-input') {
            customRadio.checked = true;
            chosenValue = 'custom';
        }
        userChoices[currentStepIndex].replacement = (chosenValue === 'custom') ? customInput.value : chosenValue;
        document.querySelectorAll('.suggestion-item').forEach(item => item.classList.remove('selected'));
        const selectedRadio = document.querySelector('input[name="replacement"]:checked');
        if (selectedRadio) selectedRadio.closest('.suggestion-item').classList.add('selected');
    }

    function restoreStepChoice(index) {
        const choice = userChoices[index].replacement;
        const original = userChoices[index].original;
        let radioToSelect = document.querySelector(`input[name="replacement"][value="${CSS.escape(choice)}"]`);
        if (radioToSelect) {
            radioToSelect.checked = true;
        } else if (choice !== original) {
            radioToSelect = document.querySelector('input[name="replacement"][value="custom"]');
            radioToSelect.checked = true;
            document.getElementById('custom-input').value = choice;
        }
        if (radioToSelect) radioToSelect.closest('.suggestion-item').classList.add('selected');
    }

    function updateStepperNav() {
        prevStepBtn.disabled = currentStepIndex === 0;
        const isLastStep = currentStepIndex === anonymizationSteps.length - 1;
        nextStepBtn.classList.toggle('hidden', isLastStep);
        finalizeBtn.classList.toggle('hidden', !isLastStep);
    }

    function updateProgressBar() {
        const progress = (currentStepIndex + 1) / anonymizationSteps.length * 100;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `Step ${currentStepIndex + 1} of ${anonymizationSteps.length}`;
    }

    function navigateStep(direction) {
        currentStepIndex += direction;
        if (currentStepIndex >= 0 && currentStepIndex < anonymizationSteps.length) {
            renderStep(currentStepIndex);
        } else {
            currentStepIndex = Math.max(0, Math.min(currentStepIndex, anonymizationSteps.length - 1));
        }
    }

    async function finalizeSpacyAnonymization() {
        showLoading(true, "Finalizing your report...");
        spacyStepper.classList.add('hidden');
        try {
            const response = await fetch('/anonymize-text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    model: 'spacy',
                    original_text: originalText,
                    choices: userChoices
                })
            });
            const data = await response.json();
            showLoading(false);
            if (response.ok) displayFinalResult(data);
            else showError(data.error || 'Failed to finalize the report.');
        } catch (error) {
            showLoading(false);
            showError('An error occurred while finalizing the report.');
        }
    }

    async function startGptProcess() {
        try {
            const response = await fetch('/anonymize-text', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model: 'chatgpt', original_text: originalText, level: levelSelect.value})
            });
            const data = await response.json();
            showLoading(false);
            if (response.ok) displayFinalResult(data);
            else showError(data.error || 'Failed to get response from AI.');
        } catch (error) {
            showLoading(false);
            showError('An error occurred while communicating with the AI model.');
        }
    }

    function displayFinalResult(data) {
        currentFinalOutput.highlighted = data.anonymized_text_highlighted;
        currentFinalOutput.clean = data.anonymized_text_clean;
        anonymizedOutput.innerHTML = currentFinalOutput.highlighted;
        outputSection.classList.remove('hidden');

        // --- THIS IS THE UPDATED LOGIC ---
        const outputTagsContainer = document.getElementById('output-info-tags');
        if (outputTagsContainer) {
            const selectedModel = modelSelect.value;
            const selectedLevel = levelSelect.value;

            const modelIcon = selectedModel === 'spacy' ? 'tune' : 'smart_toy';
            const modelText = selectedModel === 'spacy' ? 'SpaCy' : 'Advanced AI';
            const levelText = selectedLevel.charAt(0).toUpperCase() + selectedLevel.slice(1);

            outputTagsContainer.innerHTML = `
                <span class="info-tag model-${selectedModel}">
                    <span class="material-icons-outlined">${modelIcon}</span>
                    ${modelText}
                </span>
                <span class="info-tag level-${selectedLevel}">
                    <span class="material-icons-outlined">shield</span>
                    Level: ${levelText}
                </span>
            `;
        }
        // --- END OF UPDATE ---

        outputSection.scrollIntoView({behavior: 'smooth'});
    }

    async function saveReport() {
        if (!currentFinalOutput.clean) {
            showError("Nothing to save.");
            return;
        }
        try {
            const response = await fetch('/save-report', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    original_text: originalText,
                    anonymized_text_highlighted: currentFinalOutput.highlighted,
                    anonymized_text_clean: currentFinalOutput.clean,
                    model: modelSelect.value,
                    level: levelSelect.value
                })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                window.location.href = data.redirect_url;
            } else {
                showError(data.error || 'Failed to save the report.');
            }
        } catch (error) {
            showError('An error occurred while saving.');
        }
    }

    function openDownloadModal(fileType) {
        downloadFileType = fileType;
        downloadModal.classList.remove('hidden');
        document.getElementById('download-with-highlight').onclick = () => {
            showInfo(`For formatted PDF/DOCX, please save and download from the history page.`);
            downloadModal.classList.add('hidden');
        };
        document.getElementById('download-without-highlight').onclick = () => {
            showInfo(`For formatted PDF/DOCX, please save and download from the history page.`);
            downloadModal.classList.add('hidden');
        };
    }

    function showLoading(show, message = "Loading...") {
        startBtn.disabled = show;
        startBtn.innerHTML = show ? message : `<span class="material-icons-outlined">play_arrow</span>Start Anonymization`;
        loadingSpinner.querySelector('p').textContent = message;
        loadingSpinner.classList.toggle('hidden', !show);
    }

    function showMessage(message, type) {
        const mainContainer = document.querySelector('.main-container');
        const existingMessages = document.querySelector('.flash-messages');
        if (existingMessages) existingMessages.remove();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flash-messages';
        messageDiv.innerHTML = `<div class="flash flash-${type}">${message}</div>`;
        mainContainer.prepend(messageDiv);
        window.scrollTo(0, 0);
        setTimeout(() => messageDiv.remove(), 5000);
    }

    function showError(message) {
        showMessage(message, 'danger');
    }

    function showInfo(message) {
        showMessage(message, 'info');
    }

    // --- Attach All Event Listeners Safely ---
    originalTextInput.addEventListener('change', () => {
        originalText = originalTextInput.value;
    });
    clearTextBtn.addEventListener('click', () => {
        originalTextInput.value = '';
        originalText = '';
        fileUpload.value = '';
        fileNameSpan.textContent = '';
        resetUI();
    });
    fileUpload.addEventListener('change', handleFileUpload);
    startBtn.addEventListener('click', handleStart);
    levelSelect.addEventListener('change', updateLevelDescription);
    prevStepBtn.addEventListener('click', () => navigateStep(-1));
    nextStepBtn.addEventListener('click', () => navigateStep(1));
    finalizeBtn.addEventListener('click', finalizeSpacyAnonymization);
    saveReportBtn.addEventListener('click', saveReport);
    downloadPdfBtn.addEventListener('click', () => openDownloadModal('pdf'));
    downloadDocxBtn.addEventListener('click', () => openDownloadModal('docx'));
    downloadModal.addEventListener('click', (e) => {
        if (e.target.id === 'cancel-download' || e.target === downloadModal) {
            downloadModal.classList.add('hidden');
        }
    });
});