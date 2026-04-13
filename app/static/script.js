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
const chatHistory = document.getElementById("chat-history");
const queryForm = document.getElementById("query-form");
const questionInput = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");

// --- File Upload ---

// Click anywhere on drop zone to trigger file picker
dropZone.addEventListener("click", () => fileInput.click());

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

    showUploadStatus("Uploading and processing...", "loading");

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
            `${data.files_processed} file(s) processed — ${data.chunks_created} chunks created`,
            "success"
        );

        // Enable the chat input
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    } catch (err) {
        showUploadStatus("Upload failed. Please try again.", "error");
    }
}

function showUploadStatus(message, type) {
    uploadStatus.textContent = message;
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

    // Show thinking indicator
    const thinkingEl = addMessage("Searching documents and generating answer...", "thinking");

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

function addMessage(text, type) {
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.textContent = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

function addAnswer(answer, sources) {
    const div = document.createElement("div");
    div.className = "message assistant";

    // Answer text
    const answerP = document.createElement("p");
    answerP.textContent = answer;
    div.appendChild(answerP);

    // Source cards
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement("div");
        sourcesDiv.className = "sources";

        const label = document.createElement("div");
        label.className = "sources-label";
        label.textContent = "Sources";
        sourcesDiv.appendChild(label);

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
            sourcesDiv.appendChild(card);
        }

        div.appendChild(sourcesDiv);
    }

    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// --- Start ---
initSession();
