// 既有 DOM 元素
const chatBox = document.getElementById("chat-box");
const inputEl = document.getElementById("input");
const modeEl = document.getElementById("mode");
const sendBtn = document.getElementById("send-btn");
const statusText = document.getElementById("status-text");
const modeHintEl = document.getElementById("mode-hint"); // 新增：模式提示文字

let messages = loadMessages();
renderAllMessages();

// 送出事件
sendBtn.addEventListener("click", handleSend);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

// 模式切換時更新 UI
modeEl.addEventListener("change", (e) => {
  updateModeUI(e.target.value);
});

// 初始載入時套一次模式提示
updateModeUI(modeEl.value);

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
    body: JSON.stringify({ mode, messages }),
  })
    .then((res) => res.json())
    .then((data) => {
      const replyText = data.reply || "（沒有收到回覆）";
      const botMsg = { role: "assistant", content: replyText };
      messages.push(botMsg);
      saveMessages();
      appendMessageToUI(botMsg);
    })
    .catch((err) => {
      console.error(err);
      const errMsg = {
        role: "assistant",
        content: "發生錯誤，稍後再試一次。",
      };
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

// ---------- 模式切換：不同情境提示 ----------

function updateModeUI(mode) {
  if (!inputEl || !modeHintEl) return;

  if (mode === "cbt") {
    inputEl.placeholder =
      "試著寫下：發生了什麼事？在哪裡？跟誰？那一瞬間你腦中跳出的第一個念頭是什麼？";
    modeHintEl.textContent =
      "先從『事件』和『當下的想法、感受』開始就很好，不需要寫得完整。";
  } else if (mode === "act") {
    inputEl.placeholder =
      "可以寫寫：現在讓你最在意的事情是什麼？這件事對你來說，代表了什麼樣的價值？";
    modeHintEl.textContent =
      "我們不急著把情緒變好，只是一起看看：在這些感受背後，你在乎的是什麼。";
  } else if (mode === "grounding") {
    inputEl.placeholder =
      "試著描述：你現在在哪裡？身體貼著的椅子、床或地板感覺如何？周圍看得到、聽得到什麼？";
    modeHintEl.textContent =
      "當不知道要說什麼時，也可以只打：『我現在很亂，可以幫我慢慢穩下來嗎？』。";
  } else if (mode === "education") {
    inputEl.placeholder =
      "想了解哪一個主題呢？例如：焦慮、憂鬱、恐慌、CBT、Grounding 練習、壓力調適…";
    modeHintEl.textContent =
      "這個模式比較像『心理小講堂』，你可以問任何想理解的心理相關問題。";
  } else {
    // support 預設
    inputEl.placeholder =
      "可以隨便寫一小段：今天發生了什麼、卡住的地方、或只是現在的心情。";
    modeHintEl.textContent =
      "( ˶'ᵕ'🫶)💕 不需要一次寫得很多，只要比剛剛多一點點就好。";
  }
}
