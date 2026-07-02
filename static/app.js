const STORAGE_KEY = "whatsapp_sender_api_base";

function getApiBase() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) return saved.replace(/\/$/, "");
  if (window.APP_CONFIG && window.APP_CONFIG.apiBase) {
    return window.APP_CONFIG.apiBase.replace(/\/$/, "");
  }
  return "";
}

function isLocalApp() {
  return window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
}

function isUnifiedApp() {
  const host = window.location.hostname;
  return (
    isLocalApp() ||
    host.endsWith(".hf.space") ||
    host.includes("huggingface.co")
  );
}

function resolveApiBase() {
  if (isUnifiedApp()) return "";
  return getApiBase();
}

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
const backendUrlInput = document.getElementById("backend-url");
const saveBackendBtn = document.getElementById("save-backend");
const backendStatus = document.getElementById("backend-status");
const qrPanel = document.getElementById("qr-panel");
const qrImage = document.getElementById("qr-image");
const qrMessage = document.getElementById("qr-message");

const backendCard = document.getElementById("backend-card");

let sending = false;

function updateStepLabels() {
  const labels = document.querySelectorAll(".step-label");
  const offset = isUnifiedApp() ? 0 : 1;
  const numbers = ["1.", "2.", "3."];
  labels.forEach((label, index) => {
    label.textContent = numbers[index + offset] || `${index + 1 + offset}.`;
  });
}

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
  qrPanel.classList.add("hidden");
  qrImage.removeAttribute("src");
}

function showQrCode(base64Image, message) {
  qrPanel.classList.remove("hidden");
  qrImage.src = `data:image/png;base64,${base64Image}`;
  qrMessage.textContent = message || "Scan this QR code with WhatsApp on your phone.";
}

function initBackendSettings() {
  updateStepLabels();

  if (isUnifiedApp()) {
    backendCard.classList.add("hidden");
    return;
  }

  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    backendUrlInput.value = saved;
    showStatus(backendStatus, "success", "Sender connected.", [saved]);
  } else {
    showStatus(
      backendStatus,
      "warning",
      "Paste the backend URL from start-public.sh to enable sending.",
      ["Excel import works without a backend. Sending needs the free tunnel URL."]
    );
  }
}

function saveBackendUrl() {
  const value = backendUrlInput.value.trim().replace(/\/$/, "");
  if (!value) {
    localStorage.removeItem(STORAGE_KEY);
    showStatus(backendStatus, "warning", "Backend URL cleared.");
    return;
  }

  if (!/^https?:\/\/.+/i.test(value)) {
    showStatus(backendStatus, "error", "Enter a valid URL starting with http:// or https://");
    return;
  }

  localStorage.setItem(STORAGE_KEY, value);
  showStatus(backendStatus, "success", "Sender connected.", [value]);
}

async function importExcel(file) {
  importStatus.classList.remove("hidden");
  showStatus(importStatus, "warning", "Checking Excel file...");

  try {
    const buffer = await file.arrayBuffer();
    const phones = window.parseExcelPhoneList(buffer, file.name);
    phonesInput.value = phones.join("\n");
    updateSummary();
    showStatus(importStatus, "success", `Imported ${phones.length} phone numbers successfully.`);
  } catch (error) {
    showStatus(
      importStatus,
      "error",
      error.message || "Import failed.",
      error.details || []
    );
  }
}

function ensureBackendReady() {
  const apiBase = resolveApiBase();
  if (!isUnifiedApp() && !apiBase) {
    throw new Error(
      "Connect the sender first. Use the main online app or paste your backend URL in step 1."
    );
  }
  return apiBase;
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

  let apiBase;
  try {
    apiBase = ensureBackendReady();
  } catch (error) {
    alert(error.message);
    return;
  }

  sending = true;
  sendBtn.disabled = true;
  resetProgress();
  progressPanel.classList.remove("hidden");
  progressText.textContent = "Starting send job...";

  try {
    const response = await fetch(`${apiBase}/api/send`, {
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
  if (event.type === "qr") {
    showQrCode(event.image, event.message);
    progressText.textContent = event.message;
    return;
  }

  if (event.type === "status") {
    progressText.textContent = event.message;
    return;
  }

  if (event.type === "progress") {
    qrPanel.classList.add("hidden");
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
saveBackendBtn.addEventListener("click", saveBackendUrl);

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

initBackendSettings();
updateSummary();
