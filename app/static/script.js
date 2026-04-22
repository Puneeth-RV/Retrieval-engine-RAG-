let sessionId = null;

// --- Client-side limits (mirror backend) ---
const MAX_FILES = 5;
const MAX_FILE_SIZE_MB = 10;
const ALLOWED_EXT = [".pdf", ".txt"];
const MAX_QUESTION_LEN = 2000;
const QUERY_TIMEOUT_MS = 90_000;
const UPLOAD_TIMEOUT_MS = 180_000;

// --- Safely extract a server error message from a Response ---
async function safeErrorMessage(res, fallback) {
    try {
        const data = await res.json();
        if (typeof data?.detail === "string") return data.detail;
        if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    } catch (_) { /* body wasn't JSON */ }
    return fallback;
}

// --- fetch with timeout via AbortController ---
async function fetchWithTimeout(url, options = {}, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } finally {
        clearTimeout(timer);
    }
}

// --- Initialize session on page load (retry once on failure) ---
async function initSession() {
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            const res = await fetch("/api/session");
            if (!res.ok) throw new Error(`status ${res.status}`);
            const data = await res.json();
            if (!data?.session_id) throw new Error("missing session_id");
            sessionId = data.session_id;
            return;
        } catch (err) {
            if (attempt === 1) {
                showUploadStatus(
                    "Couldn't connect to the server. Refresh the page to try again.",
                    "error"
                );
            }
        }
    }
}

// --- DOM elements ---
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const fileChips = document.getElementById("file-chips");
const chatSection = document.getElementById("chat-section");
const chatHistory = document.getElementById("chat-history");
const queryForm = document.getElementById("query-form");
const questionInput = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");

// --- File Upload ---

// Click anywhere on drop zone to trigger file picker
// (but not if clicking the label/button, which already triggers it)
dropZone.addEventListener("click", (e) => {
    if (e.target.closest(".file-label")) return;
    fileInput.click();
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

function validateFiles(files) {
    if (files.length > MAX_FILES) {
        return `Too many files. Maximum ${MAX_FILES} per upload.`;
    }
    for (const file of files) {
        const name = file.name || "file";
        const dot = name.lastIndexOf(".");
        const ext = dot === -1 ? "" : name.slice(dot).toLowerCase();
        if (!ALLOWED_EXT.includes(ext)) {
            return `"${name}" is not a supported type. Use PDF or TXT.`;
        }
        if (file.size === 0) {
            return `"${name}" is empty.`;
        }
        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
            const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
            return `"${name}" is ${sizeMb}MB. Maximum is ${MAX_FILE_SIZE_MB}MB.`;
        }
    }
    return null;
}

async function handleFiles(files) {
    if (!files.length) return;

    if (!sessionId) {
        showUploadStatus("Session not ready yet. Please refresh the page.", "error");
        return;
    }

    // Client-side validation before hitting the server
    const validationError = validateFiles(files);
    if (validationError) {
        showUploadStatus(validationError, "error");
        return;
    }

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
        const res = await fetchWithTimeout(
            "/api/upload",
            { method: "POST", body: formData },
            UPLOAD_TIMEOUT_MS
        );

        if (!res.ok) {
            const msg = await safeErrorMessage(res, "Upload failed. Please try again.");
            showUploadStatus(msg, "error");
            return;
        }

        const data = await res.json();
        showUploadStatus(
            `${data.files_processed} file(s) processed &mdash; ${data.chunks_created} chunks created`,
            "success"
        );

        // Reveal chat section and enable the input
        chatSection.style.display = "";
        document.body.classList.remove("state-empty");
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    } catch (err) {
        const msg = err?.name === "AbortError"
            ? "Upload timed out. Try a smaller file."
            : "Upload failed. Check your connection and try again.";
        showUploadStatus(msg, "error");
    } finally {
        // Always re-enable drop zone
        dropZone.style.pointerEvents = "";
        dropZone.style.opacity = "";
    }
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

    if (!sessionId) {
        addMessage("Session not ready. Please refresh the page.", "assistant");
        return;
    }

    if (question.length > MAX_QUESTION_LEN) {
        addMessage(
            `Your question is too long (${question.length} chars). Please keep it under ${MAX_QUESTION_LEN}.`,
            "assistant"
        );
        return;
    }

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
        const res = await fetchWithTimeout(
            "/api/query",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, question }),
            },
            QUERY_TIMEOUT_MS
        );

        if (!res.ok) {
            thinkingEl.remove();
            const msg = await safeErrorMessage(res, "Something went wrong.");
            addMessage(msg, "assistant");
            return;
        }

        await streamAnswer(res, thinkingEl);
    } catch (err) {
        thinkingEl.remove();
        const msg = err?.name === "AbortError"
            ? "The request took too long and was cancelled. Try a shorter question or try again."
            : "Failed to get a response. Check your connection and try again.";
        addMessage(msg, "assistant");
    } finally {
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
});

async function streamAnswer(res, thinkingEl) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let answerText = "";
    let sources = [];
    let answerContent = null;
    let messageDiv = null;
    let firstToken = true;
    let errored = false;

    const renderAnswer = () => {
        if (answerContent) answerContent.innerHTML = formatAnswer(answerText);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
            if (!line.trim()) continue;
            let evt;
            try { evt = JSON.parse(line); } catch { continue; }

            if (evt.type === "sources") {
                sources = evt.sources || [];
            } else if (evt.type === "token") {
                if (firstToken) {
                    thinkingEl.remove();
                    clearEmptyState();
                    messageDiv = document.createElement("div");
                    messageDiv.className = "message assistant";
                    answerContent = document.createElement("div");
                    answerContent.className = "answer-content";
                    messageDiv.appendChild(answerContent);
                    chatHistory.appendChild(messageDiv);
                    firstToken = false;
                }
                answerText += evt.text;
                renderAnswer();
            } else if (evt.type === "error") {
                thinkingEl.remove();
                addMessage(evt.message || "Something went wrong.", "assistant");
                errored = true;
            }
        }
    }

    if (errored) return;

    if (firstToken) {
        thinkingEl.remove();
        addMessage("No answer returned. Please try a different question.", "assistant");
        return;
    }

    if (sources.length > 0 && messageDiv) {
        appendSources(messageDiv, sources);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

function appendSources(parentDiv, sources) {
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
    parentDiv.appendChild(sourcesDiv);
}

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

// --- Theme Toggle ---
const themeToggle = document.getElementById("theme-toggle");

function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
}

// Load saved theme or default to dark
const savedTheme = localStorage.getItem("theme") || "light";
setTheme(savedTheme);

themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    setTheme(current === "dark" ? "light" : "dark");
});

// --- Random tagline ---
const TAGLINES = [
    "Shred through the fine print.",
    "Skip the scrolling. Just ask.",
    "Crack open your documents.",
    "Stop reading. Start asking.",
    "Dig into your docs.",
    "Every page, one question away.",
    "Rip through the pages.",
    "Cut straight to the answer.",
    "Interrogate your PDFs.",
    "Turn pages into answers.",
    "No more Ctrl+F.",
    "Don't read. Ask.",
];
const taglineEl = document.getElementById("tagline");
if (taglineEl) {
    taglineEl.textContent = TAGLINES[Math.floor(Math.random() * TAGLINES.length)];
}

// --- Start ---
initSession();
