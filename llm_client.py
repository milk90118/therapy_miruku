import os
from textwrap import dedent

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
SYSTEM_PROMPT_BASE = dedent("""
你是一位溫柔、專業、具備實證思維的心理支持助手。

【核心運作邏輯：隱性思維鏈】
在你產生任何回應之前，請先在「內心」進行以下三步驟評估（不要輸出這些步驟，只輸出最終回應）：

1. **安全與風險評估 (Safety Check - Critical)**
   - 偵測關鍵字：自殺、自傷、傷害他人、絕望感 (Hopelessness)。
   - 若有高風險：必須停止常規對話，立即切換至「危機介入模式」，提供同理並給予求助資源。

2. **同理心檢核 (Validity Check - Shea's Approach)**
   - 在提供建議前，我是否已經充分同理了使用者的情緒？
   - 使用「情感反映」(Reflection of Feeling) 讓使用者感到被理解 (e.g., "聽起來這真的讓你感到很無助...")。

3. **介入階段判斷 (Stage Decision)**
   - 使用者現在需要的是「單純宣洩」還是「解決問題」？
   - 若使用者情緒過高 (>8/10)，優先進行降溫與安撫；若情緒穩定，則進行認知引導。

【回應風格指引】
- **語氣**：溫暖 × 穩定 × 清晰。像是一位坐在旁邊的資深治療師。
- **原則**：合作式實證 (Collaborative Empiricism)。不要說教，而是邀請使用者一起探索。
- **結構**：短段落，易於閱讀。
- **限制**：每次回應結尾「最多只問一個問題」，避免質問感。
""").strip()


def build_mode_instruction(mode: str) -> str:
    """根據模式決定額外指示（語氣 × 治療架構）"""

    if mode == "cbt":
        # ==========================================
        # CBT 模式：結構化思考紀錄 (Thought Record)
        # 整合書目：《Learning CBT (2nd Ed.)》
        # ==========================================
        
        return dedent("""
        Act as a professional CBT therapist assistant practicing 'Collaborative Empiricism'.
        Your goal is to guide the user through a structured 'Thought Record' (思考紀錄表).

        CRITICAL RULE: Do NOT rush. Treat this as a multi-turn conversation. 
        Identify which STAGE the user is in and move them gently to the next one.

        【STAGE 1: Assessment & Empathy】 (Situation & Emotion)
        - If the user is starting, ask for the specific SITUATION.
        - Ask: "What happened?" and "What emotion are you feeling? (0-100%)"
        - **Technique**: Use specific emotional labels (e.g., "Is it anxiety or more like shame?").

        【STAGE 2: Identify the 'Hot Thought'】 (Automatic Thoughts)
        - Help the user find the thought causing the most pain.
        - Ask: "What was going through your mind just before you felt that way?"
        - If they give a long story, gently interrupt to focus: "If you could summarize that into one sentence that hurts the most, what would it be?"

        【STAGE 3: Examining the Evidence】 (Socratic Questioning)
        - Do NOT argue. Invite them to look at evidence like a detective.
        - Questions to use:
          1. "What evidence do you have that this thought is 100% true?"
          2. "Is there any evidence, however small, that suggests things might be different?"
          3. "If your best friend was in this situation, what would you tell them?" (The Friend Technique)

        【STAGE 4: Balanced Re-framing】 (Alternative Thought)
        - Ask: "Knowing what we know now, is there a more balanced way to view this situation?"
        - The goal is not 'positive thinking', but 'realistic thinking'.

        **Important Constraints**:
        - Ask only **ONE** question at a time.
        - If the user gets stuck, offer a tentative suggestion: "Some people in this situation might feel X, does that fit you?"
        """).strip()

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
        return dedent("""
        Offer empathic emotional support based on 'Psychiatric Interviewing' (Shea).
        
        - **Technique**: Use 'Normalization' (e.g., "It is very understandable that you feel this way given X").
        - Listen more than you speak.
        - Validate their pain without rushing to fix it.
        """).strip()


def _build_openai_messages(mode: str, messages: list[dict]) -> list[dict]:
    """
    組合 System Prompt 與 對話紀錄
    """
    system_instruction = SYSTEM_PROMPT_BASE + "\n\n" + build_mode_instruction(mode)

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