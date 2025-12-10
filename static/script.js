// =========================
// DOM Element 取得
// =========================
const chatBox = document.getElementById("chat-box");
const inputEl = document.getElementById("input");
const modeEl = document.getElementById("mode");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");   // ⬅ 新增
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
/* 主事件綁定 */
// =========================
if (sendBtn) {
  sendBtn.addEventListener("click", handleSend);
}

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
  modeEl.addEventListener("change", (e) => {
    updateModeUI(e.target.value);
  });
  // 初始套一次
  updateModeUI(modeEl.value);
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
      setTimeout(() => {
        statusText.textContent = "";
      }, 1500);
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
      const errMsg = {
        role: "assistant",
        content: "發生錯誤，稍後再試一次。",
      };
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
// 模式提示：不同 mode 不同 placeholder/hint
// =========================
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

  // 櫻花：增加到 35 片，營造更豐富的春日氛圍
  if (sakuraContainer) {
    for (let i = 0; i < 35; i++) {
      const petal = document.createElement("div");
      petal.className = "sakura";
      
      // 隨機分佈於螢幕寬度
      petal.style.left = Math.random() * 100 + "%";
      
      // 隨機延遲，避免同時出現
      petal.style.animationDelay = Math.random() * 12 + "s";
      
      // 隨機持續時間，創造深度感
      petal.style.animationDuration = 12 + Math.random() * 8 + "s";
      
      sakuraContainer.appendChild(petal);
    }
  }

  // 星星：增加到 40 顆，營造滿天星空
  if (starContainer) {
    for (let i = 0; i < 40; i++) {
      const star = document.createElement("div");
      star.className = "star";
      
      // 隨機分佈於整個螢幕
      star.style.left = Math.random() * 100 + "%";
      star.style.top = Math.random() * 100 + "%";
      
      // 隨機延遲與持續時間
      star.style.animationDelay = Math.random() * 4 + "s";
      star.style.animationDuration = 3 + Math.random() * 3 + "s";
      
      starContainer.appendChild(star);
    }
  }
});