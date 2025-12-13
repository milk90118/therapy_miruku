// =========================
// DOM Element 取得
// =========================
const chatBox = document.getElementById("chat-box");
const inputEl = document.getElementById("input");
const modeEl = document.getElementById("mode");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const statusText = document.getElementById("status-text");
const modeHintEl = document.getElementById("mode-hint");

const themeToggle = document.getElementById("theme-toggle");
const themeIcon = themeToggle ? themeToggle.querySelector(".theme-icon") : null;
const html = document.documentElement;

// =========================
// LocalStorage：歷史訊息
// =========================
let messages = loadMessages();
renderAllMessages();

// =========================
// 主事件綁定
// =========================
if (sendBtn) sendBtn.addEventListener("click", handleSend);

if (inputEl) {
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
}

// 模式切換 → 更新 placeholder & hint
if (modeEl) {
  modeEl.addEventListener("change", (e) => updateModeUI(e.target.value));
  updateModeUI(modeEl.value); // 初始套一次
}

// 清除對話 → 開一個新的 session 感覺
if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    if (!confirm("確定要清除這一段對話，重新開始嗎？")) return;

    messages = [];
    saveMessages();
    renderAllMessages();

    if (statusText) {
      statusText.textContent = "已開始新的對話 🌱";
      setTimeout(() => (statusText.textContent = ""), 1500);
    }
  });
}

// =========================
// 送出訊息
// =========================
function handleSend() {
  if (!inputEl) return;

  const text = inputEl.value.trim();
  if (!text) return;

  const mode = modeEl ? modeEl.value : "support";

  const userMsg = { role: "user", content: text };
  messages.push(userMsg);
  saveMessages();
  appendMessageToUI(userMsg);

  inputEl.value = "";
  callBackend(mode);
}

// =========================
// 呼叫後端 /api/chat
// =========================
function callBackend(mode) {
  if (sendBtn) sendBtn.disabled = true;
  if (statusText) statusText.textContent = "思考中…";

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
      const errMsg = { role: "assistant", content: "發生錯誤，稍後再試一次。" };
      messages.push(errMsg);
      saveMessages();
      appendMessageToUI(errMsg);
    })
    .finally(() => {
      if (sendBtn) sendBtn.disabled = false;
      if (statusText) statusText.textContent = "";
    });
}

// =========================
// UI 渲染
// =========================
function appendMessageToUI(msg) {
  if (!chatBox) return;

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
  if (!chatBox) return;
  chatBox.innerHTML = "";
  messages.forEach(appendMessageToUI);
}

// =========================
// LocalStorage 存取
// =========================
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

// =========================
// 模式提示：三種 mode 專屬 placeholder/hint
// =========================
function updateModeUI(mode) {
  if (!inputEl || !modeHintEl) return;

  if (mode === "cbt") {
    inputEl.placeholder =
      "先寫三件事：①發生了什麼（事件）②當下第一個念頭（想法）③身體/情緒反應（感受）";
    modeHintEl.textContent =
      "不用完美：只要把『事件—想法—感受』寫出來一點點，我們就能開始整理。";
  } else if (mode === "分析性" || mode === "analytic" || mode === "psychodynamic") {
    inputEl.placeholder =
      "可以寫：你最在意的那一段互動/感受是什麼？它像不像過去某種熟悉的模式？";
    modeHintEl.textContent =
      "我們會慢慢來：先澄清、再探究；若你願意，才會輕輕碰觸更深的『為什麼』。";
  } else {
    // support（溫柔陪伴）
    inputEl.placeholder =
      "可以隨便寫一小段：今天卡住的地方、最重的一種感覺、或只是你想被聽見的那句話。";
    modeHintEl.textContent =
      "( ˶'ᵕ'🫶)💕 不需要一次寫很多，只要比剛剛多一點點就好。";
  }
}

// =========================
// 主題切換（日 / 夜）
// =========================
(function initTheme() {
  if (!themeToggle || !themeIcon) return;

  const savedTheme = localStorage.getItem("theme") || "light";
  html.setAttribute("data-theme", savedTheme);
  themeIcon.textContent = savedTheme === "dark" ? "☀️" : "🌙";

  themeToggle.addEventListener("click", () => {
    const currentTheme = html.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    html.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
    themeIcon.textContent = newTheme === "dark" ? "☀️" : "🌙";
  });
})();

// =========================
// 櫻花 & 星星自動生成 - 增加數量與層次
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const sakuraContainer = document.querySelector(".sakura-container");
  const starContainer = document.querySelector(".star-container");

  // 櫻花
  if (sakuraContainer) {
    for (let i = 0; i < 35; i++) {
      const petal = document.createElement("div");
      petal.className = "sakura";
      petal.style.left = Math.random() * 100 + "%";
      petal.style.animationDelay = Math.random() * 12 + "s";
      petal.style.animationDuration = 12 + Math.random() * 8 + "s";
      sakuraContainer.appendChild(petal);
    }
  }

  // 星星
  if (starContainer) {
    for (let i = 0; i < 40; i++) {
      const star = document.createElement("div");
      star.className = "star";
      star.style.left = Math.random() * 100 + "%";
      star.style.top = Math.random() * 100 + "%";
      star.style.animationDelay = Math.random() * 4 + "s";
      star.style.animationDuration = 3 + Math.random() * 3 + "s";
      starContainer.appendChild(star);
    }
  }
});
