const API_BASE = (window.APP_CONFIG && window.APP_CONFIG.apiBase) || "";

const messageInput = document.getElementById("message");
const phonesInput = document.getElementById("phones");
const delayInput = document.getElementById("delay");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const excelInput = document.getElementById("excel-file");
const uploadBox = document.getElementById("upload-box");
const importStatus = document.getElementById("import-status");
const summaryCount = document.getElementById("summary-count");
const summaryMessage = document.getElementById("summary-message");
const progressPanel = document.getElementById("progress-panel");
const progressFill = document.getElementById("progress-fill");
const progressText = document.getElementById("progress-text");
const logList = document.getElementById("log-list");

let sending = false;

function parsePhones(text) {
  return text
    .split(/[\n,;]+/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function updateSummary() {
  const count = parsePhones(phonesInput.value).length;
  const message = messageInput.value.trim();
  summaryCount.textContent = `${count} number${count === 1 ? "" : "s"}`;
  summaryMessage.textContent = message
    ? `Message: ${message.slice(0, 60)}${message.length > 60 ? "..." : ""}`
    : "No message yet";
}

function showStatus(element, type, title, details = []) {
  element.classList.remove("hidden", "success", "error", "warning");
  element.classList.add(type);
  const detailHtml = details.length
    ? `<ul>${details.map((item) => `<li>${item}</li>`).join("")}</ul>`
    : "";
  element.innerHTML = `<strong>${title}</strong>${detailHtml}`;
}

function resetProgress() {
  progressPanel.classList.add("hidden");
  progressFill.style.width = "0%";
  progressText.textContent = "Preparing...";
  logList.innerHTML = "";
}

async function importExcel(file) {
  importStatus.classList.remove("hidden");
  showStatus(importStatus, "warning", "Checking Excel file...");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/api/import-excel`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (!response.ok) {
      const details = data.detail?.details || [];
      showStatus(
        importStatus,
        "error",
        data.detail?.message || data.detail || "Import failed.",
        details
      );
      return;
    }

    phonesInput.value = data.phones.join("\n");
    updateSummary();
    showStatus(importStatus, "success", data.message);
  } catch (error) {
    showStatus(importStatus, "error", "Could not import the Excel file.", [String(error)]);
  }
}

async function startSend() {
  if (sending) return;

  const message = messageInput.value.trim();
  const phones = parsePhones(phonesInput.value);
  const delaySeconds = Number(delayInput.value || 5);

  if (!message) {
    alert("Please type a message first.");
    return;
  }

  if (!phones.length) {
    alert("Please add at least one phone number.");
    return;
  }

  sending = true;
  sendBtn.disabled = true;
  resetProgress();
  progressPanel.classList.remove("hidden");
  progressText.textContent = "Starting send job...";

  try {
    const response = await fetch(`${API_BASE}/api/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        phones,
        delay_seconds: delaySeconds,
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Send request failed.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const line = chunk.trim();
        if (!line.startsWith("data:")) continue;
        const event = JSON.parse(line.slice(5).trim());
        handleEvent(event);
      }
    }
  } catch (error) {
    progressText.textContent = `Error: ${error.message}`;
    const item = document.createElement("li");
    item.className = "fail";
    item.textContent = error.message;
    logList.prepend(item);
  } finally {
    sending = false;
    sendBtn.disabled = false;
  }
}

function handleEvent(event) {
  if (event.type === "status") {
    progressText.textContent = event.message;
    return;
  }

  if (event.type === "progress") {
    const percent = Math.round((event.current / event.total) * 100);
    progressFill.style.width = `${percent}%`;
    progressText.textContent = event.message;
    return;
  }

  if (event.type === "result") {
    const item = document.createElement("li");
    item.className = event.success ? "ok" : "fail";
    item.textContent = `${event.phone}: ${event.detail}`;
    logList.prepend(item);
    return;
  }

  if (event.type === "complete") {
    progressFill.style.width = "100%";
    progressText.textContent = `Done. Sent ${event.sent} of ${event.total}. Failed: ${event.failed}.`;
    return;
  }

  if (event.type === "error") {
    progressText.textContent = `Error: ${event.message}`;
  }
}

messageInput.addEventListener("input", updateSummary);
phonesInput.addEventListener("input", updateSummary);
sendBtn.addEventListener("click", startSend);

clearBtn.addEventListener("click", () => {
  messageInput.value = "";
  phonesInput.value = "";
  importStatus.classList.add("hidden");
  resetProgress();
  updateSummary();
});

excelInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (file) importExcel(file);
});

uploadBox.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadBox.classList.add("dragover");
});

uploadBox.addEventListener("dragleave", () => {
  uploadBox.classList.remove("dragover");
});

uploadBox.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadBox.classList.remove("dragover");
  const file = event.dataTransfer.files?.[0];
  if (file) importExcel(file);
});

updateSummary();
