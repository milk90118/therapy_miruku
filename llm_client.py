import os
from textwrap import dedent

from dotenv import load_dotenv
from openai import OpenAI

from cbt_mode import build_cbt_instruction
from psy_interview_prompt import build_psy_interview_instruction
from supportive_mode import build_supportive_prompt
from analytic_mode import build_analytic_prompt


# =========================
# API Key / Client bootstrap
# =========================

# ① 優先讀系統環境變數（給 Render 用）
api_key = os.getenv("OPENAI_API_KEY")

# ② 本機如果沒有，再讀 .env
if not api_key:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found. Set it in environment or .env")

client = OpenAI(api_key=api_key)

# 預設模型
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_model_name(mode: str) -> str:
    """
    未來如果想讓不同模式用不同模型，可以在這裡集中管理。
    """
    # 目前所有 mode 共用同一個模型
    return OPENAI_MODEL


# ==========================================
# 核心系統提示詞 (The Brain & Safety Guard)
# ==========================================

SYSTEM_PROMPT_BASE = (
    dedent(
        """
        你是一位溫柔、專業、具備實證思維的心理支持助手。

        【核心運作邏輯：隱性思維鏈】
        在你產生任何回應之前，請先在「內心」進行以下三步驟評估（不要輸出這些步驟，只輸出最終回應）：

        1. **安全與風險評估 (Safety Check - Critical)**
           - 偵測關鍵字：自殺、自傷、傷害他人、絕望感 (Hopelessness)。
           - 若有高風險：必須停止常規對話，立即切換至「危機介入模式」，提供同理並給予求助資源。

        2. **同理心檢核 (Validity Check)**
           - 在提供建議前，先用情感反映確認自己有沒有抓到對方的心情。
           - 優先接住情緒，再往下問細節。

        3. **介入階段判斷 (Stage Decision)**
           - 判斷使用者現在主要需要的是：宣洩 / 被理解、還是問題解決與規劃。
           - 若情緒非常強烈，先穩定與安撫；情緒較穩時，再進入認知或行為面的整理。

        【回應風格指引】
        - 語氣：溫暖 × 穩定 × 清晰，像是一位坐在旁邊的資深治療師，聚焦在核心引導使用者說更多。
        - 原則：合作式實證 (Collaborative Empiricism)，與使用者一起看證據、一起思考。
        - 結構：段落清楚，便於在手機上閱讀。
        - 限制：每次回應結尾「最多只問一個聚焦問題」或只給一個小任務，避免像在審問。
        - 禁止：多餘的寒暄語句 (例如「希望這對你有幫助」等)。
        """
    ).strip()
    + "\n\n"
    + build_psy_interview_instruction()
)

# - 禁止：診斷用語、長篇心理教育、連續問多題、括號內補充、清單/符號列點、引用規則。
#     - 若使用者提供很多細節：只抓一個最核心感受回應，其餘留給提問邀請。
OUTPUT_RULES = dedent(
    """
    【輸出格式（一般情況必遵守）】
    - 使用繁體中文，總長度 **50-120 字**（含標點；不含空白）。記住使用者的個人細節。
    - 根據回話長度調整細節多寡，避免過長或過短。
    【例外（安全優先）】
    - 若偵測自傷/自殺/他傷高風險：立即危機介入與求助資源，字數可放寬，但仍保持簡短清晰。
    """
).strip()


def build_mode_instruction(mode: str, messages: list[dict] | None = None) -> str:
    """
    根據 mode 產生額外指示（語氣 × 治療架構）
    - 重要：分析性模式需要 messages 才能在 analytic_mode.py 內自動 routing 子模式
    """
    mode_key = (mode or "").strip()

    # 用 wrapper 統一呼叫介面（避免不同函式簽名造成錯誤）
    mode_map = {
        "cbt": lambda m: build_cbt_instruction(),
        "support": lambda m: build_supportive_prompt(),
        "supportive": lambda m: build_supportive_prompt(),
        "default": lambda m: build_supportive_prompt(),
        "分析性": lambda m: build_analytic_prompt(messages=m),
        "psychodynamic": lambda m: build_analytic_prompt(messages=m),
        "analytic": lambda m: build_analytic_prompt(messages=m),
    }

    fn = mode_map.get(mode_key, lambda m: build_supportive_prompt())
    return fn(messages)


def _build_openai_messages(mode: str, messages: list[dict] | None) -> list[dict]:
    """
    組合 System Prompt 與 對話紀錄
    """
    messages = messages or []

    system_instruction = (
        OUTPUT_RULES
        + "\n\n"
        + SYSTEM_PROMPT_BASE
        + "\n\n"
        + build_mode_instruction(mode, messages=messages)
    )

    openai_messages: list[dict] = [{"role": "system", "content": system_instruction}]

    for m in messages:
        role = (m.get("role") or "user").strip()
        content = m.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        content = content.strip()
        if not content:
            continue

        # 確保 role 只有 user 或 assistant
        if role not in ("user", "assistant"):
            role = "user"

        openai_messages.append({"role": role, "content": content})

    return openai_messages


def generate_reply(mode: str, messages: list[dict]) -> str:
    """
    主函式：呼叫 OpenAI API
    """
    try:
        openai_messages = _build_openai_messages(mode, messages)
        model_name = get_model_name(mode)

        # 保留你原本的 Responses API 用法
        response = client.responses.create(
            model=model_name,
            input=openai_messages,
        )

        # 解析回傳（相容性處理）
        reply_text = None

        if hasattr(response, "output_text") and response.output_text:
            reply_text = response.output_text
        else:
            # 常見 Responses 結構 fallback
            try:
                reply_text = response.output[0].content[0].text.value
            except Exception:
                # 再 fallback（若被以 chat.completions 類結構回傳）
                try:
                    reply_text = response.choices[0].message.content
                except Exception:
                    reply_text = "（系統繁忙，請稍後再試。）"

        return (reply_text or "").strip()

    except Exception as e:
        return f"連線發生錯誤：{e}\n請檢查網路或 API Key 設定。"
