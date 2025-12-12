import os
import time
import random
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

# ✅ Step 1: 治療師短回覆鎖
OUTPUT_RULES = dedent("""
【治療師短回覆規則（一般情況必遵守）】
- 繁體中文；單段落；總長度 80–100 字（不含空白、含標點）。
- 嚴格 3 句（不得加第 4 句、不得條列）：
  1) 反映：用「聽起來／我感覺」抓住一個核心情緒或衝突。
  2) 聚焦：用一句話縮小到「此刻最關鍵的一點」（可給一個很小的下一步，但不說教、不解釋原理）。
  3) 開放式問句：只問 1 題、用「你願意／可以」開頭，邀請多說具體細節。
- 禁止：長篇心理教育、連問多題、診斷語氣、括號補充、清單符號、寒暄開場（你好/很高興你來這裡…）。
【例外】
- 若出現自傷/自殺/他傷高風險：優先危機介入與求助資源，可不受字數限制，但仍保持簡短清楚。
""").strip()


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

    return build_supportive_prompt()


# ✅ Step 2: OUTPUT_RULES 放在 mode 指令之前
def _build_instructions(mode: str) -> str:
    return SYSTEM_PROMPT_BASE + "\n\n" + build_mode_instruction(mode) + "\n\n" + OUTPUT_RULES


def _build_input_messages(messages: list[dict]) -> list[dict]:
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


# ✅ Step 5: 指數退避重試（精簡版）
def _retry_with_backoff(callable_fn, max_retries: int = 3):
    for attempt in range(max_retries + 1):
        try:
            return callable_fn()
        except Exception:
            if attempt >= max_retries:
                raise
            sleep_s = (0.6 * (2 ** attempt)) + random.uniform(0, 0.4)
            time.sleep(sleep_s)


def generate_reply(
    mode: str,
    messages: list[dict],
    *,
    previous_response_id: str | None = None,
) -> tuple[str, str | None]:
    instructions = _build_instructions(mode)
    input_messages = _build_input_messages(messages)
    model_name = get_model_name(mode)

    try:
        resp_kwargs: dict[str, Any] = dict(
            model=model_name,
            instructions=instructions,
            input=input_messages,
            # ✅ Step 3: 硬上限，穩住 80–100 字輸出（可依實測微調）
            max_output_tokens=170,  # max_output_tokens 是 Responses API 的輸出上限
            # ✅ Step 4: 心理內容預設不存（可自行改 True）
            store=False,
        )

        # previous_response_id 可串接狀態；且 instructions 不會自動繼承，所以你每次重送是正確的
        if previous_response_id:
            resp_kwargs["previous_response_id"] = previous_response_id

        response = _retry_with_backoff(lambda: client.responses.create(**resp_kwargs))

        reply_text = (response.output_text or "").strip()
        if not reply_text:
            reply_text = "（系統繁忙，請稍後再試。）"

        return reply_text, getattr(response, "id", None)

    except Exception as e:
        return f"連線發生錯誤：{e}\n請檢查網路或 API Key 設定。", None
