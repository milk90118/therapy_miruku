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

# 預設模型（可由環境變數覆蓋）
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_model_name(mode: str) -> str:
    """
    未來如果想讓不同模式用不同模型，可以在這裡集中管理。
    目前統一用 CP 值最高的 mini。
    """
    base_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    return base_model


SYSTEM_PROMPT_BASE = dedent("""
你是一位溫柔、專業、具備實證思維的心理支持助手。

【核心指令】
在回應使用者之前，請先在內心（不需要輸出）進行以下評估：
1. **風險評估**：是否有自殺、自傷或傷害他人的風險？（若有，必須立刻提供求助資源）
2. **同理檢核**：我是否已經充分同理了使用者的情緒？（Shea's Validity Techniques）
3. **階段判斷**：使用者的問題現在需要的是「傾聽宣洩」還是「解決方案」？

【回應原則】
- 使用溫暖、柔和、短段落的方式回應。
- 嚴禁說教 (No lecturing)。
- 每次回應結尾最多只問「一個」問題，避免讓使用者感到壓力。
- 以「我們」取代「你」（例如：「我們可以怎麼看這件事？」），建立治療同盟。

請以「溫暖 × 穩定 × 清晰」的風格回應。
""").strip()


def build_mode_instruction(mode: str) -> str:
    """根據模式決定額外指示（語氣 × 治療情境）"""

    if mode == "cbt":
        # CBT：結構化思考紀錄
        return dedent("""
        Act as a professional CBT therapist assistant. Your goal is to guide the user through a 'Thought Record' exercise.
        
        CRITICAL RULE: Do NOT ask all questions at once. Proceed step-by-step.
        Check the chat history to determine which STAGE the user is currently in:

        [STAGE 1: Situation & Emotion]
        - If the user just started, ask what happened (Situation) and how they feel (Emotion).
        - Use 'Empathy First': Validate their feeling before analyzing it.
        - Ask: "What was going through your mind at that moment?"

        [STAGE 2: Identify Automatic Thoughts]
        - Help the user catch the specific 'Hot Thought' that caused the strongest distress.
        - Label Cognitive Distortions if clear (e.g., "It sounds like you might be Catastrophizing...").

        [STAGE 3: Examine Evidence (The Socratic Method)]
        - Do not argue. Ask gently:
          "What is the evidence that this thought is true?"
          "Is there any evidence that this might not be 100% true?"
        - Look for alternative explanations.

        [STAGE 4: Balanced Thought]
        - Ask: "Knowing what we know now, how could we rephrase that thought to be more accurate?"

        [Tone Guidelines]
        - Use Socratic Questioning (e.g., "What makes you feel that way?" instead of "You shouldn't feel that way").
        - Be patient. One question at a time.
        - If the user is in crisis, abandon CBT and switch to Safety/Support mode immediately.
        """).strip()

    elif mode == "act":
        # ACT：接納 × 價值 × 小行動
        return dedent("""
        Act as an ACT (Acceptance and Commitment Therapy)–informed companion.
        This is a gentle ACT reflection space, not formal therapy.

        - Welcome all thoughts and emotions with acceptance; do not try to erase or fix them quickly.
        - Invite the user to NOTICE their thoughts and bodily sensations, as passing experiences.
        - Ask about what truly MATTERS to them (values) in this situation.
        - Gently suggest 1–2 very small, values-based actions they could try, without pressure.
        - Use validating, non-judgmental language; emphasize 'it's okay to feel this way'.
        """).strip()

    elif mode == "grounding":
        # Grounding：安撫 × 回到當下
        return dedent("""
        Act as a grounding and self-soothing assistant.
        This is a short grounding exercise space, focusing on the present moment.

        - Use very slow, gentle, and reassuring language.
        - Invite the user to notice their breathing, body contact with chair/bed, and the room around them.
        - Offer simple exercises, like: 5-4-3-2-1 senses scan, counting breaths, feeling feet on the floor.
        - Keep explanations minimal; focus on 'what to do now' in 1–2 small steps.
        - If the user describes intense panic or feeling unsafe, remind them to seek in-person help if possible.
        """).strip()

    elif mode == "education":
        # 心理教育：清楚、有條理
        return dedent("""
        Provide psychoeducation in clear, simple language.
        This is an educational explanation mode, not a counseling session.

        - Explain psychological concepts (e.g., anxiety, depression, CBT, grounding, stress) in everyday words.
        - Use short bullet points and concrete daily-life examples.
        - Avoid jargon; if you must use a term, explain it briefly.
        - Emphasize that this is general information and does not replace personal medical or psychological advice.
        """).strip()

    else:  # support（預設：溫柔陪伴聊天）
        return dedent("""
        Offer empathic emotional support.
        This is a gentle, supportive conversation space.

        - Start by acknowledging what the user shared and reflecting their feelings.
        - Normalize common reactions without minimizing their pain.
        - Ask simple, open questions to understand a bit more, but do not push.
        - Suggest 1–2 small coping ideas (breathing, journaling, reaching out to someone they trust), not a long checklist.
        - Avoid diagnoses or strong promises; use steady, honest, and kind language.
        """).strip()



def _build_openai_messages(mode: str, messages: list[dict]) -> list[dict]:
    """
    把系統指令 + 前端傳進來的 messages 組成 OpenAI Responses API 的 input 格式
    messages: [{"role": "user"|"assistant", "content": "text"}, ...]
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
        if role not in ("user", "assistant"):
            role = "user"
        openai_messages.append(
            {"role": role, "content": content}
        )

    return openai_messages


def generate_reply(mode: str, messages: list[dict]) -> str:
    """
    主函式：被 app.py 呼叫
    mode: "support" / "cbt" / "education"
    messages: 來自前端的對話歷史 [{"role": "...", "content": "..."}]
    """
    try:
        openai_messages = _build_openai_messages(mode, messages)
        model_name = get_model_name(mode)

        response = client.responses.create(
            model=model_name,
            input=openai_messages,
        )

        # 和你 test_openai_key.py 一樣，用 output_text 取得文字（若有）
        if hasattr(response, "output_text") and response.output_text:
            reply_text = response.output_text
        else:
            # 後備方案（避免 Response 結構變動時整個掛掉）
            try:
                # 新版 Responses API 常見結構：output[0].content[0].text.value
                reply_text = (
                    response.output[0]
                    .content[0]
                    .text.value
                )
            except Exception:
                reply_text = "（已呼叫模型，但無法解析回傳內容。）"

        return reply_text.strip()

    except Exception as e:
        # 回傳錯誤訊息給前端
        return f"發生錯誤：{e}\n請稍後再試，或檢查伺服器 log。"
