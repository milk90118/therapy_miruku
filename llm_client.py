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

請遵守以下原則：
- 使用溫暖、柔和、短段落的方式回應。
- 以理解、陪伴、穩定情緒為優先。
- 鼓勵使用者進行自我照顧，並在需要時尋求適當的專業協助。
- 不提供診斷、不取代真正的心理師或醫師。
- 若使用者提及自傷、他傷或高度風險情境，溫柔但明確地提醒他立即尋求醫療與在地緊急資源。
- 保持溫度，但也維持專業界線；不評論、不批判、不過度承諾。

你的語氣像：
- 安靜的陪伴、輕柔的引導、能讓人安心呼吸的那種溫度。
- 但清楚、可靠，讓人覺得安全。

請以「溫暖 × 穩定 × 清晰」的風格回應。
""").strip()


def build_mode_instruction(mode: str) -> str:
    """根據模式決定額外指示（語氣 × 治療情境）"""

    if mode == "cbt":
        # CBT：結構化思考紀錄
        return dedent("""
        Act as a CBT (cognitive behavioral therapy) thought record assistant.
        This is a structured CBT note-taking session, not casual chat.

        - First, briefly ask the user to describe the SITUATION (what happened, when, where, with whom).
        - Then help them identify AUTOMATIC THOUGHTS and EMOTIONS (0–100%).
        - Gently guide them to explore EVIDENCE FOR / AGAINST their thoughts.
        - Finally, co-create 1–2 ALTERNATIVE, more balanced thoughts together.
        - Ask only 1–2 focused questions at a time. Keep it step-by-step.
        - Avoid giving any diagnosis; focus on patterns and possible new perspectives.
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
