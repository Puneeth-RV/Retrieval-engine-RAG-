let sessionId = null;

// --- Initialize session on page load ---
async function initSession() {
    const res = await fetch("/api/session");
    const data = await res.json();
    sessionId = data.session_id;
}

// --- DOM elements ---
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const fileChips = document.getElementById("file-chips");
const chatHistory = document.getElementById("chat-history");
const queryForm = document.getElementById("query-form");
const questionInput = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");

// --- File Upload ---

// Click anywhere on drop zone to trigger file picker
// (but not if clicking the label/button, which already triggers it)
dropZone.addEventListener("click", (e) => {
    if (e.target === dropZone || e.target.classList.contains("drop-text") ||
        e.target.classList.contains("drop-subtext") || e.target.classList.contains("drop-hint")) {
        fileInput.click();
    }
});

// Drag and drop styling
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    handleFiles(e.dataTransfer.files);
});

// File input change
fileInput.addEventListener("change", () => {
    handleFiles(fileInput.files);
    fileInput.value = ""; // reset so same file can be re-uploaded
});

async function handleFiles(files) {
    if (!files.length) return;

    // Show file chips
    showFileChips(files);

    // Disable drop zone during upload
    dropZone.style.pointerEvents = "none";
    dropZone.style.opacity = "0.5";

    showUploadStatus(
        `<span class="spinner"></span> Processing ${files.length} file(s)...`,
        "loading"
    );

    const formData = new FormData();
    formData.append("session_id", sessionId);
    for (const file of files) {
        formData.append("files", file);
    }

    try {
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            showUploadStatus(err.detail || "Upload failed", "error");
            return;
        }

        const data = await res.json();
        showUploadStatus(
            `${data.files_processed} file(s) processed &mdash; ${data.chunks_created} chunks created`,
            "success"
        );

        // Enable the chat input
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    } catch (err) {
        showUploadStatus("Upload failed. Please try again.", "error");
    }

    // Re-enable drop zone
    dropZone.style.pointerEvents = "";
    dropZone.style.opacity = "";
}

function showFileChips(files) {
    fileChips.innerHTML = "";
    for (const file of files) {
        const chip = document.createElement("div");
        chip.className = "file-chip";
        const icon = file.name.endsWith(".pdf")
            ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
            : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>';
        chip.innerHTML = `${icon} ${file.name}`;
        fileChips.appendChild(chip);
    }
    fileChips.hidden = false;
}

function showUploadStatus(message, type) {
    uploadStatus.innerHTML = message;
    uploadStatus.className = `upload-status ${type}`;
    uploadStatus.hidden = false;
}

// --- Chat / Query ---

queryForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = questionInput.value.trim();
    if (!question) return;

    // Show user message
    addMessage(question, "user");
    questionInput.value = "";

    // Show thinking indicator with animated dots
    const thinkingEl = document.createElement("div");
    thinkingEl.className = "message thinking";
    thinkingEl.innerHTML = '<span class="spinner"></span> Searching documents and generating answer<span class="dots"></span>';
    chatHistory.appendChild(thinkingEl);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    // Disable input while processing
    questionInput.disabled = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, question }),
        });

        // Remove thinking indicator
        thinkingEl.remove();

        if (!res.ok) {
            const err = await res.json();
            addMessage(err.detail || "Something went wrong.", "assistant");
        } else {
            const data = await res.json();
            addAnswer(data.answer, data.sources);
        }
    } catch (err) {
        thinkingEl.remove();
        addMessage("Failed to get a response. Please try again.", "assistant");
    }

    // Re-enable input
    questionInput.disabled = false;
    sendBtn.disabled = false;
    questionInput.focus();
});

function clearEmptyState() {
    const empty = chatHistory.querySelector(".empty-state");
    if (empty) empty.remove();
}

function addMessage(text, type) {
    clearEmptyState();
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.textContent = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

function formatAnswer(text) {
    // Process line by line for clean, predictable output
    const lines = text.split("\n");
    let html = "";
    let inList = false;
    let listType = "";

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // Escape HTML
        line = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

        // Apply inline formatting
        line = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        line = line.replace(/`([^`]+)`/g, "<code>$1</code>");

        // Headings: ## Heading or ### Heading
        if (/^#{2,3}\s+/.test(line)) {
            if (inList) { html += `</${listType}>`; inList = false; }
            const content = line.replace(/^#{2,3}\s+/, "");
            html += `<h4>${content}</h4>`;
            continue;
        }

        // Numbered list: "1. item"
        if (/^\d+\.\s+/.test(line)) {
            const content = line.replace(/^\d+\.\s+/, "");
            if (!inList || listType !== "ol") {
                if (inList) html += `</${listType}>`;
                html += "<ol>";
                inList = true;
                listType = "ol";
            }
            html += `<li>${content}</li>`;
            continue;
        }

        // Bullet list: "- item" or "* item"
        if (/^[-*]\s+/.test(line)) {
            const content = line.replace(/^[-*]\s+/, "");
            if (!inList || listType !== "ul") {
                if (inList) html += `</${listType}>`;
                html += "<ul>";
                inList = true;
                listType = "ul";
            }
            html += `<li>${content}</li>`;
            continue;
        }

        // Close any open list
        if (inList) {
            html += `</${listType}>`;
            inList = false;
        }

        // Empty line = paragraph break
        if (line.trim() === "") {
            continue;
        }

        // Regular text
        html += `<p>${line}</p>`;
    }

    // Close any remaining open list
    if (inList) {
        html += `</${listType}>`;
    }

    return html;
}

function addAnswer(answer, sources) {
    const div = document.createElement("div");
    div.className = "message assistant";

    // Answer text — render with formatting
    const answerDiv = document.createElement("div");
    answerDiv.className = "answer-content";
    answerDiv.innerHTML = formatAnswer(answer);
    div.appendChild(answerDiv);

    // Collapsible source cards
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement("div");
        sourcesDiv.className = "sources";

        const toggle = document.createElement("button");
        toggle.className = "sources-toggle";
        toggle.innerHTML = `<span class="toggle-arrow">&#9654;</span> Sources (${sources.length})`;
        sourcesDiv.appendChild(toggle);

        const sourcesList = document.createElement("div");
        sourcesList.className = "sources-list collapsed";

        for (const source of sources) {
            const card = document.createElement("div");
            card.className = "source-card";

            const filename = document.createElement("span");
            filename.className = "source-filename";
            filename.textContent = source.filename;

            const score = document.createElement("span");
            score.className = "source-score";
            score.textContent = `(${(source.score * 100).toFixed(1)}% match)`;

            const preview = document.createElement("div");
            preview.className = "source-preview";
            preview.textContent = source.text_preview;

            card.appendChild(filename);
            card.appendChild(score);
            card.appendChild(preview);
            sourcesList.appendChild(card);
        }

        toggle.addEventListener("click", () => {
            sourcesList.classList.toggle("collapsed");
            toggle.classList.toggle("open");
        });

        sourcesDiv.appendChild(sourcesList);
        div.appendChild(sourcesDiv);
    }

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// --- Theme Toggle ---
const themeToggle = document.getElementById("theme-toggle");

function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
}

// Load saved theme or default to dark
const savedTheme = localStorage.getItem("theme") || "dark";
setTheme(savedTheme);

themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    setTheme(current === "dark" ? "light" : "dark");
});

// --- Start ---
initSession();
