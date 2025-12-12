import os
from textwrap import dedent
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from cbt_mode import build_cbt_instruction
from psy_interview_prompt import build_psy_interview_instruction
from supportive_mode import build_supportive_prompt


# =====================
# OpenAI client setup
# =====================
def _get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found. Set it in environment or .env")
    return api_key


client = OpenAI(api_key=_get_api_key())

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_model_name(mode: str) -> str:
    # 需要時可做 mode -> model mapping
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


# ==========================================
# System Instructions (Brain + Safety Guard)
# ==========================================
SYSTEM_PROMPT_BASE = (
    dedent("""
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
    - 限制：每次回應結尾「最多只問一個聚焦問題」或只給一個小任務，避免像在審問。
    """).strip()
    + "\n\n"
    + build_psy_interview_instruction()
)


def build_mode_instruction(mode: str) -> str:
    if mode == "cbt":
        return build_cbt_instruction()

    if mode == "act":
        return dedent("""
        Act as an ACT (Acceptance and Commitment Therapy) companion.
        Focus on: Defusion (脫鉤), Acceptance (接納), and Values (價值).

        - Defusion: "I am having the thought that ..."
        - Acceptance: use metaphors (passing cloud / passenger on a bus)
        - Values: "Deep down, what kind of person do you want to be in this moment?"
        - Action: one tiny step aligned with values
        """).strip()

    if mode == "grounding":
        return dedent("""
        Act as a grounding assistant. Bring the user back to the here-and-now.
        - Very short, simple sentences.
        - 5-4-3-2-1 senses exercise.
        - Breathing: inhale 4, hold 7, exhale 8.
        """).strip()

    if mode == "education":
        return dedent("""
        Provide psychoeducation in clear, layman terms.
        Structure: 1) Definition 2) Mechanism 3) What helps
        """).strip()

    # default: support
    return build_supportive_prompt()


def _build_instructions(mode: str) -> str:
    return SYSTEM_PROMPT_BASE + "\n\n" + build_mode_instruction(mode)


def _build_input_messages(messages: list[dict]) -> list[dict]:
    """
    Responses API 的 input：建議只放 user/assistant
    """
    out: list[dict] = []
    for m in messages:
        role = m.get("role", "user")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role not in ("user", "assistant"):
            role = "user"
        out.append({"role": role, "content": content})
    return out


def generate_reply(
    mode: str,
    messages: list[dict],
    *,
    previous_response_id: str | None = None,
) -> tuple[str, str | None]:
    """
    回傳 (reply_text, response_id)
    - 如果你想省 token：下一輪把 response_id 丟回 previous_response_id
    """
    instructions = _build_instructions(mode)
    input_messages = _build_input_messages(messages)
    model_name = get_model_name(mode)

    try:
        resp_kwargs: dict[str, Any] = dict(
            model=model_name,
            instructions=instructions,   # ✅ system prompt 放這裡
            input=input_messages,        # ✅ 只放 user/assistant
        )
        if previous_response_id:
            resp_kwargs["previous_response_id"] = previous_response_id

        response = client.responses.create(**resp_kwargs)

        reply_text = (response.output_text or "").strip()
        if not reply_text:
            reply_text = "（系統繁忙，請稍後再試。）"

        return reply_text, getattr(response, "id", None)

    except Exception as e:
        return f"連線發生錯誤：{e}\n請檢查網路或 API Key 設定。", None
