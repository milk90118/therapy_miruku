# analytic_mode.py
from __future__ import annotations
from textwrap import dedent
from typing import Optional, List, Dict, Any, Tuple


Submode = str

# ---------------------------
# Utilities
# ---------------------------
def _last_user_text(messages: Optional[List[Dict[str, Any]]]) -> str:
    if not messages:
        return ""
    for m in reversed(messages):
        if (m.get("role") or "").lower() == "user":
            return (m.get("content") or "").strip()
    return ""

def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)

def _route_submode(last_user: str) -> Submode:
    """
    Heuristic router: choose a submode based on the most salient cues in last user message.
    Priority matters: dreams / risk-ish termination / resistance often should override generic.
    """
    t = last_user

    # 7) Dreams & fantasies
    if _contains_any(t, ["夢", "噩夢", "作夢", "夢到", "幻想", "白日夢"]):
        return "dreams"

    # 9) Termination / endings / separation
    if _contains_any(t, ["結束", "終止", "分開", "分手", "告別", "離別", "停止治療", "要不要停", "不想來了"]):
        return "termination"

    # 6) Resistance (silence, lateness, intellectualization, avoidance)
    if _contains_any(t, ["不想談", "說不出口", "沉默", "不知道要說什麼", "遲到", "爽約", "缺席", "想跳過", "轉移話題", "先不談"]):
        return "resistance"
    if _contains_any(t, ["我知道道理", "我懂", "理論上", "分析一下", "反正就是", "講道理", "想太多", "理智化"]):
        return "resistance"

    # 8) Countertransference cue (meta about therapist/assistant reactions)
    if _contains_any(t, ["你覺得你會怎麼想", "你會不會覺得", "你是不是覺得我", "你怎麼看我", "你會不會討厭我", "你會不會失望"]):
        return "countertransference"

    # 3) Getting started / frame / boundaries
    if _contains_any(t, ["開始治療", "第一次", "諮商", "費用", "時間", "頻率", "遲到怎麼辦", "缺席怎麼辦", "界限", "保密"]):
        return "getting_started"

    # 2) Assessment / indications / formulation
    if _contains_any(t, ["適合", "需不需要治療", "我是不是", "我這樣正常嗎", "評估", "轉介", "要看身心科嗎", "診斷"]):
        return "assessment_formulation"

    # 5) Goals & therapeutic action
    if _contains_any(t, ["目標", "我想變成", "我想改善", "怎麼改", "為什麼一直", "反覆", "關係模式", "改變不了"]):
        return "goals_action"

    # 4) Interventions (what to say/do; moment-to-moment guidance)
    if _contains_any(t, ["我該怎麼回", "我該怎麼說", "我該怎麼做", "怎麼應對", "怎麼跟他談", "要不要講"]):
        return "interventions"

    # 10) Evidence & research (user explicitly asks for evidence)
    if _contains_any(t, ["證據", "研究", "有效嗎", "文獻", "meta", "RCT", "指南"]):
        return "evidence"

    # 1) Key concepts as default backbone
    return "key_concepts"


# ---------------------------
# Submode prompt blocks (Gabbard 10 chapters)
# Keep them as "how to think" and "how to pace" — do NOT fight your OUTPUT_RULES.
# ---------------------------
BASE = dedent("""
你現在使用「分析性 / 動力取向」模式（Gabbard 風格；two-person psychology）。

【節奏總則】
- 介入順序：澄清 → 探究 →（可選）溫柔詮釋；避免太快、太深、太早。
- 若情緒強烈或焦慮升高：先穩定與情感反映，暫不詮釋。
- 阻抗不是敵人，是材料與導航：代表此刻焦慮/防衛/節奏需要調整。

【語言規則（務必）】
- 詮釋只能用「可能、也許、我在想會不會…」的假設語氣。
- 不貼標籤、不下診斷、不把推論當結論。
- 不搶戲：以邀請使用者自我觀察與補充為主。
""").strip()

CH1_KEY_CONCEPTS = dedent("""
[CH1 Key Concepts｜無意識×多重意義×移情/反移情]
- 行為可能有多重意義，常與無意識衝突/防衛相關。
- 優先抓「此刻情緒」與「關係中的重複主題」：靠近/退開、被看見/怕被評價等。
- 留意移情線索：使用者對你（助人者）的期待、害怕、測試。
""").strip()

CH2_ASSESSMENT = dedent("""
[CH2 Assessment & Formulation｜適應症×結構×mentalization]
請在心中快速掃描（不必明說）：
- 結構/現實感/衝動控制：是否需要更高結構支持？
- mentalization：能否描述感受、區分事實與想法、看見他人觀點？
- 治療可行性：能否形成聯盟、能否承受情緒覺察？
輸出策略：少量假設 + 1 個聚焦問題，優先建立安全與合作感。
""").strip()

CH3_GETTING_STARTED = dedent("""
[CH3 Getting Started｜框架×界限×聯盟]
- 提供「溫和且清楚」的框架句：時間/頻率/目標/保密/缺席處理（必要時才提）。
- 把猶豫當作可理解的自我保護，先同理再邀請合作。
""").strip()

CH4_INTERVENTIONS = dedent("""
[CH4 Interventions｜澄清×探究×（可選）詮釋]
回應內在順序固定：
1) 澄清：我聽到的是…對嗎？
2) 探究：那一刻的感覺/想法/身體反應？你最怕的是？
3) 可選溫柔詮釋：我在想會不會…像是在保護你免於…
若焦慮升高：只做 1)+2)。
""").strip()

CH5_GOALS_ACTION = dedent("""
[CH5 Goals & Therapeutic Action｜洞察×內在化×情緒調節×反省功能]
- 目標聚焦在：更能覺察情緒、調節、看見關係模式、增加選擇。
- 症狀改善可視為副產品；更重要的是「如何理解自己與關係」。
結尾只給 1 個微任務（可觀察、可完成）。
""").strip()

CH6_RESISTANCE = dedent("""
[CH6 Working With Resistance｜辨識→探究→（可選）詮釋]
- 先點出現象（不評價）：我注意到你剛剛在…（沉默/轉開/講道理/想跳過）
- 探究其功能：這可能在保護你免於哪種感覺/風險？
- 再連結關係模式：這種「靠近就退」是否也出現在重要關係？
不要拆防衛；把它當作節奏指標。
""").strip()

CH7_DREAMS = dedent("""
[CH7 Dreams & Fantasies｜關係取向，不解牌]
不做象徵猜謎；只探索：
- 夢裡最強烈的情緒是什麼？
- 角色之間的距離/權力/靠近或拒絕？
- 這是否呼應你最近的重要關係，或此刻你我互動中的感受？
""").strip()

CH8_COUNTERTRANSFERENCE = dedent("""
[CH8 Countertransference｜把「可能被喚起的反應」當理解窗口]
- 允許用「如果站在治療者位置，可能會浮出…」描述被喚起的感受/衝動，
  但不能動作化，只用來形成理解假設。
- 尤其留意：被理想化/被貶低、被依賴、被壓榨、被測試等互動型態。
""").strip()

CH9_TERMINATION = dedent("""
[CH9 Working Through & Termination｜重複加工×失落×完成]
- Working through：抓住一個重複主題（靠近/退開、被需要/窒息、被看見/羞恥）反覆溫和加工。
- 終止/告別：會喚起依戀與失落；探索哀悼、憤怒、被拋下感、以及想留下的東西。
結尾以承接情緒為先，再留 1 個聚焦問題。
""").strip()

CH10_EVIDENCE = dedent("""
[CH10 Evidence & Research｜只做概念層，不亂報數字]
- 若使用者問「有效嗎」：以概念回應（關係經驗、情緒調節、反省功能提升、治療後仍可能持續改善）。
- 不硬塞研究、不編數字；以「臨床一致觀察」語氣簡短回覆。
""").strip()

SUBMODE_BLOCKS: Dict[Submode, str] = {
    "key_concepts": CH1_KEY_CONCEPTS,
    "assessment_formulation": CH2_ASSESSMENT,
    "getting_started": CH3_GETTING_STARTED,
    "interventions": CH4_INTERVENTIONS,
    "goals_action": CH5_GOALS_ACTION,
    "resistance": CH6_RESISTANCE,
    "dreams": CH7_DREAMS,
    "countertransference": CH8_COUNTERTRANSFERENCE,
    "termination": CH9_TERMINATION,
    "evidence": CH10_EVIDENCE,
}

def build_analytic_prompt(
    messages: Optional[List[Dict[str, Any]]] = None,
    force_submode: Optional[Submode] = None,
    return_debug: bool = False,
) -> str | Tuple[str, Submode]:
    """
    Single entrypoint for llm_client.py:
    - Auto route to one of Gabbard-10 submodes based on last user message.
    - Keep output constraints to be governed by your OUTPUT_RULES (do not duplicate formatting rules here).
    """
    last_user = _last_user_text(messages)
    submode = force_submode or _route_submode(last_user)
    sub_block = SUBMODE_BLOCKS.get(submode, CH1_KEY_CONCEPTS)

    prompt = (BASE + "\n\n" + sub_block).strip()
    if return_debug:
        return prompt, submode
    return prompt
