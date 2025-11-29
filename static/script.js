const chatBox = document.getElementById("chat-box");
const inputEl = document.getElementById("input");
const modeEl = document.getElementById("mode");
const sendBtn = document.getElementById("send-btn");
const statusText = document.getElementById("status-text");

let messages = loadMessages();

renderAllMessages();

sendBtn.addEventListener("click", handleSend);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

function handleSend() {
  const text = inputEl.value.trim();
  if (!text) return;

  const mode = modeEl.value;

  // push user message
  const userMsg = { role: "user", content: text };
  messages.push(userMsg);
  saveMessages();
  appendMessageToUI(userMsg);

  inputEl.value = "";
  callBackend(mode);
}

function callBackend(mode) {
  sendBtn.disabled = true;
  statusText.textContent = "思考中…";

  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, messages })
  })
    .then(res => res.json())
    .then(data => {
      const replyText = data.reply || "（沒有收到回覆）";
      const botMsg = { role: "assistant", content: replyText };
      messages.push(botMsg);
      saveMessages();
      appendMessageToUI(botMsg);
    })
    .catch(err => {
      console.error(err);
      const errMsg = { role: "assistant", content: "發生錯誤，稍後再試一次。" };
      messages.push(errMsg);
      saveMessages();
      appendMessageToUI(errMsg);
    })
    .finally(() => {
      sendBtn.disabled = false;
      statusText.textContent = "";
    });
}

function appendMessageToUI(msg) {
  const div = document.createElement("div");
  div.classList.add("msg");
  if (msg.role === "user") div.classList.add("msg-user");

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.classList.add(msg.role === "user" ? "bubble-user" : "bubble-bot");
  bubble.textContent = msg.content;

  div.appendChild(bubble);
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function renderAllMessages() {
  chatBox.innerHTML = "";
  messages.forEach(appendMessageToUI);
}

function saveMessages() {
  try {
    localStorage.setItem("therapy_messages", JSON.stringify(messages));
  } catch (e) {
    console.warn("Cannot save to localStorage", e);
  }
}

function loadMessages() {
  try {
    const raw = localStorage.getItem("therapy_messages");
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.warn("Cannot load from localStorage", e);
    return [];
  }
}
