"""
心理治療小助手 - LLM Client
Production Version (修正完成)
"""
import os
from textwrap import dedent

from cbt_mode import build_cbt_instruction
from psy_interview_prompt import build_psy_interview_instruction
from supportive_mode import build_supportive_prompt
from dotenv import load_dotenv
from openai import OpenAI

# =====================
# API Key 載入
# =====================
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found. Set it in environment or .env")

client = OpenAI(api_key=api_key)

# 預設模型（已修正）
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_model_name(mode: str) -> str:
    """依模式取得模型名稱"""
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


# ==========================================
# 核心系統提示詞
# ==========================================

# 短回覆規則（放最前面，權重最高）
OUTPUT_RULES = dedent("""
    【治療師短回覆規則 - 最高優先】
    - 繁體中文，80-120字，單段落
    - 嚴格 3 句：
      1) 反映：「聽起來／我感覺…」抓住核心情緒
      2) 聚焦：縮小到此刻最關鍵的一點
      3) 開放式問句：只問 1 題
    - 禁止：條列、多問、說教、寒暄開場
    - 例外：危機情況可不受字數限制
""").strip()

SYSTEM_PROMPT_BASE = (
    OUTPUT_RULES
    + "\n\n"
    + dedent("""
    你是一位溫柔、專業、具備實證思維的心理支持助手。

    【核心運作邏輯：隱性思維鏈】
    在你產生任何回應之前，請先在「內心」進行以下三步驟評估（不要輸出這些步驟，只輸出最終回應）：

    1. **安全與風險評估 (Safety Check - Critical)**
       - 偵測關鍵字：自殺、自傷、傷害他人、絕望感 (Hopelessness)。
       - 若有高風險：必須停止常規對話，立即切換至「危機介入模式」，提供同理並給予求助資源。

    2. **同理心檢核 (Validity Check)**
       - 在提供建議前，先用情感反映確認自己有沒有抓到對方的心情。
       - 優先用：「聽起來…」「感覺你…」來接住情緒，再往下問細節。

    3. **介入階段判斷 (Stage Decision)**
       - 判斷使用者現在主要需要的是：宣洩 / 被理解、還是問題解決與規劃。
       - 若情緒非常強烈，先穩定與安撫；情緒較穩時，再進入認知或行為面的整理。

    【回應風格指引】
    - 語氣：溫暖 × 穩定 × 清晰，像是一位坐在旁邊的資深治療師。
    - 原則：合作式實證 (Collaborative Empiricism)，與使用者一起看證據、一起思考。
    - 結構：段落清楚，便於在手機上閱讀。
    """).strip()
    + "\n\n"
    + build_psy_interview_instruction()
)


def build_mode_instruction(mode: str) -> str:
    """根據模式決定額外指示（語氣 × 治療架構）"""

    if mode == "cbt":
        return build_cbt_instruction()

    elif mode == "act":
        return dedent("""
        Act as an ACT (Acceptance and Commitment Therapy) companion.
        Focus on: Defusion (脫鉤), Acceptance (接納), and Values (價值).

        - **Defusion**: If user says "I am a failure", help them rephrase to "I am having the thought that I am a failure."
        - **Acceptance**: Use metaphors (e.g., "Treat your anxiety like a passing cloud or a passenger on a bus").
        - **Values**: Ask "Deep down, what kind of person do you want to be in this moment?"
        - **Action**: Encourage one tiny step consistent with their values, regardless of how they feel.
        """).strip()

    elif mode == "grounding":
        return dedent("""
        Act as a grounding assistant. Your goal is to bring the user back to the 'Here and Now'.
        
        - Use very short, simple sentences.
        - Direct the user to their 5 senses immediately.
        - Exercise: "Name 5 things you see, 4 things you feel, 3 things you hear..."
        - Focus on breathing: "Inhale for 4, hold for 7, exhale for 8."
        """).strip()

    elif mode == "education":
        return dedent("""
        Provide psychoeducation in clear, layman terms.
        
        - Explain concepts (CBT, Anxiety, Depression) using analogies.
        - Structure: 1. Definition, 2. Why it happens (Mechanism), 3. What helps.
        - Remind them: "Understanding is the first step to changing."
        """).strip()

    else:  # support（預設：一般支持性會談）
        return build_supportive_prompt()


def _build_openai_messages(mode: str, messages: list[dict]) -> list[dict]:
    """組合 System Prompt 與對話紀錄"""
    system_instruction = SYSTEM_PROMPT_BASE + "\n\n" + build_mode_instruction(mode)

    openai_messages: list[dict] = [
        {"role": "system", "content": system_instruction}
    ]

    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        if role not in ("user", "assistant"):
            role = "user"
        openai_messages.append({"role": role, "content": content})

    return openai_messages


def generate_reply(mode: str, messages: list[dict]) -> str:
    """主函式：呼叫 OpenAI API"""
    try:
        openai_messages = _build_openai_messages(mode, messages)
        model_name = get_model_name(mode)

        # 正確的 OpenAI Chat Completions API
        response = client.chat.completions.create(
            model=model_name,
            messages=openai_messages,
            max_tokens=250,
            temperature=0.7,
        )

        # 解析回應
        reply_text = response.choices[0].message.content
        
        if not reply_text:
            return "（系統繁忙，請稍後再試。）"
        
        return reply_text.strip()

    except Exception as e:
        error_msg = str(e).lower()
        if "api_key" in error_msg or "authentication" in error_msg:
            return "API 設定有誤，請聯繫開發者。"
        elif "rate_limit" in error_msg:
            return "目前使用人數較多，請稍後再試 🙏"
        elif "model" in error_msg:
            return "模型設定有誤，請聯繫開發者。"
        else:
            return f"連線發生錯誤，請稍後再試。\n（錯誤訊息：{e}）"