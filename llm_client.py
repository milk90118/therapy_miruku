import os
from textwrap import dedent

from dotenv import load_dotenv
from openai import OpenAI

import os
from textwrap import dedent
from dotenv import load_dotenv
from openai import OpenAI

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

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT_BASE = dedent("""
You are a supportive, evidence-informed mental health assistant.
You:
- Use gentle, short paragraphs.
- Encourage help-seeking and self-care.
- Never claim to replace a real therapist or doctor.
- Always remind users to seek local emergency help if they mention self-harm or harm to others.
- Keep a warm but professional tone.
""").strip()


def build_mode_instruction(mode: str) -> str:
    """根據模式決定額外指示"""
    if mode == "cbt":
        return dedent("""
        Act as a CBT (cognitive behavioral therapy) thought record assistant.
        - Help the user identify automatic thoughts, emotions (0–100%), and alternative balanced thoughts.
        - Ask 1–2 guiding questions at a time, not too many.
        - Focus on clarifying situations, thoughts, emotions, behaviors, and alternative viewpoints.
        """).strip()
    elif mode == "education":
        return dedent("""
        Provide psychoeducation in clear, simple language.
        - Explain psychological concepts (e.g., anxiety, depression, CBT, grounding).
        - Use short bullet points and concrete daily-life examples.
        - Avoid jargon; if you must use it, explain it.
        """).strip()
    else:  # support
        return dedent("""
        Offer empathic emotional support.
        - Reflect and validate the user's feelings.
        - Normalize common reactions without minimizing their pain.
        - Suggest 1–2 simple coping ideas (breathing, grounding, reaching out).
        - Avoid giving medical diagnoses.
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

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=openai_messages,
        )

        # 和你 test_openai_key.py 一樣，用 output_text 取得文字
        if hasattr(response, "output_text") and response.output_text:
            reply_text = response.output_text
        else:
            # 後備方案（通常用不到）
            reply_text = "（已呼叫模型，但無法解析回傳內容。）"

        return reply_text.strip()

    except Exception as e:
        # 回傳錯誤訊息給前端
        return f"發生錯誤：{e}\n請稍後再試，或檢查伺服器 log。"
