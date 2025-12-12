import os
from textwrap import dedent
from cbt_mode import build_cbt_instruction  # ⬅ 新增這行
from psy_interview_prompt import build_psy_interview_instruction  # ⬅ 新增這行
from supportive_mode import build_supportive_prompt  # ⬅ 新增這行
from dotenv import load_dotenv
from openai import OpenAI

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
    base_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    return base_model


# ==========================================
# 核心系統提示詞 (The Brain & Safety Guard)
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
    - 長度：不超過 100 字，聚焦在核心引導。
    - 語氣：溫暖 × 穩定 × 清晰，像是一位坐在旁邊的資深治療師。
    - 原則：合作式實證 (Collaborative Empiricism)，與使用者一起看證據、一起思考。
    - 結構：段落清楚，便於在手機上閱讀。
    - 限制：每次回應結尾「最多只問一個聚焦問題」或只給一個小任務，避免像在審問。
    - 禁止：多餘的寒暄語句 (例如「希望這對你有幫助」等)。       
    """).strip()
    + "\n\n"
    + build_psy_interview_instruction()
)

OUTPUT_RULES = dedent("""
【輸出格式（一般情況必遵守）】
- 使用繁體中文，總長度 **80–100 字**（含標點；不含空白）。
- 嚴格採用「3 句骨架」，不得加第四句、不得條列：
  1) 同理反映（1句）：用「聽起來／我感覺」開頭，命名情緒或壓力點。
  2) 溫柔引導（1句）：肯定努力＋給一個很小的下一步（不教訓、不長解釋）。
  3) 開放式提問（1句）：只能 1 個問題、以「你願意／可以」開頭，邀請多說細節。
- 禁止：診斷用語、長篇心理教育、連續問多題、括號內補充、清單/符號列點、引用規則。
- 若使用者提供很多細節：只抓一個最核心感受回應，其餘留給提問邀請。

【例外（安全優先）】
- 若偵測自傷/自殺/他傷高風險：立即危機介入與求助資源，字數可放寬，但仍保持簡短清晰。
""").strip()

def build_mode_instruction(mode: str) -> str:
    """根據模式決定額外指示（語氣 × 治療架構）"""

    if mode == "cbt":
        # CBT 模式指令獨立在 cbt_mode.py
        return build_cbt_instruction()

    elif mode == "act":
        # ACT：接納與承諾 (Acceptance & Commitment)
        return dedent("""
        Act as an ACT (Acceptance and Commitment Therapy) companion.
        Focus on: Defusion (脫鉤), Acceptance (接納), and Values (價值).

        - **Defusion**: If user says "I am a failure", help them rephrase to "I am having the thought that I am a failure."
        - **Acceptance**: Use metaphors (e.g., "Treat your anxiety like a passing cloud or a passenger on a bus").
        - **Values**: Ask "Deep down, what kind of person do you want to be in this moment?"
        - **Action**: Encourage one tiny step consistent with their values, regardless of how they feel.
        """).strip()

    elif mode == "grounding":
        # Grounding：著地練習 (適合恐慌/解離)
        return dedent("""
        Act as a grounding assistant. Your goal is to bring the user back to the 'Here and Now'.
        
        - Use very short, simple sentences.
        - Direct the user to their 5 senses immediately.
        - Exercise: "Name 5 things you see, 4 things you feel, 3 things you hear..."
        - Focus on breathing: "Inhale for 4, hold for 7, exhale for 8."
        """).strip()

    elif mode == "education":
        # 心理教育 (Psychoeducation)
        return dedent("""
        Provide psychoeducation in clear, layman terms.
        
        - Explain concepts (CBT, Anxiety, Depression) using analogies.
        - Structure: 1. Definition, 2. Why it happens (Mechanism), 3. What helps.
        - Remind them: "Understanding is the first step to changing."
        """).strip()

    else:  # support（預設：一般支持性會談）
        return build_supportive_prompt()


def _build_openai_messages(mode: str, messages: list[dict]) -> list[dict]:
    """
    組合 System Prompt 與 對話紀錄
    """
    system_instruction = OUTPUT_RULES + "\n\n" + SYSTEM_PROMPT_BASE + "\n\n" + build_mode_instruction(mode)

    openai_messages: list[dict] = [
        {"role": "system", "content": system_instruction}
    ]

    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        # 確保 role 只有 user 或 assistant
        if role not in ("user", "assistant"):
            role = "user"
        openai_messages.append(
            {"role": role, "content": content}
        )

    return openai_messages


def generate_reply(mode: str, messages: list[dict]) -> str:
    """
    主函式：呼叫 OpenAI API
    """
    try:
        openai_messages = _build_openai_messages(mode, messages)
        model_name = get_model_name(mode)

        # 注意：此處保留您原本的 client.responses.create 用法
        # 若未來使用標準 OpenAI SDK (v1.0+)，請改為 client.chat.completions.create
        response = client.responses.create(
            model=model_name,
            input=openai_messages,
        )

        # 嘗試解析回傳 (相容性處理)
        if hasattr(response, "output_text") and response.output_text:
            reply_text = response.output_text
        else:
            try:
                # 針對新版 API 常見的回傳結構
                reply_text = response.output[0].content[0].text.value
            except Exception:
                # 若結構再次變動，嘗試從 chat completion 結構讀取
                try:
                    reply_text = response.choices[0].message.content
                except:
                    reply_text = "（系統繁忙，請稍後再試。）"

        return reply_text.strip()

    except Exception as e:
        return f"連線發生錯誤：{e}\n請檢查網路或 API Key 設定。"