# -*- coding: utf-8 -*-
"""
Contract type router - automatically detect which contract type user wants.
"""

import re
from typing import Optional

# Supported contract types with metadata
CONTRACT_TYPES = {
    "tigong": {
        "name": "数据提供合同",
        "code": "GF-2025-2615",
        "keywords": [
            "数据提供", "提供合同", "提供方", "接收方", 
            "卖数据", "买数据", "数据交易", "数据买卖",
            "出售数据", "购买数据", "数据出让"
        ],
        "description": "适用于一方向另一方提供数据的交易场景（甲方为接收方，乙方为提供方）",
        "parties": ["甲方（接收方）", "乙方（提供方）"],
        "articles": 16,
    },
    "weituo": {
        "name": "数据委托处理服务合同",
        "code": "GF-2025-2616",
        "keywords": [
            "委托处理", "委托合同", "数据处理", "处理服务",
            "帮我处理数据", "数据加工", "数据清洗", "数据标注",
            "数据脱敏", "数据分析服务", "外包处理"
        ],
        "description": "适用于委托方将数据交给受托方进行处理的场景（甲方为委托方，乙方为受托方）",
        "parties": ["甲方（委托方）", "乙方（受托方）"],
        "articles": 18,
    },
    "ronghe": {
        "name": "数据融合开发合同",
        "code": "GF-2025-2617",
        "keywords": [
            "融合开发", "融合合同", "多方合作", "数据融合",
            "共同开发", "联合开发", "数据共建", "数据池",
            "多源数据", "数据汇聚", "联盟", "共享平台"
        ],
        "description": "适用于多方共同参与数据融合开发的场景（甲乙丙丁多方参与）",
        "parties": ["甲方（融合参与方1）", "乙方（融合参与方2）", "丙方（可选）", "丁方（可选）"],
        "articles": 14,
    },
    "zhongjie": {
        "name": "数据中介服务合同",
        "code": "GF-2025-2618",
        "keywords": [
            "中介服务", "中介合同", "撮合交易", "交易平台",
            "数据中介", "数据经纪", "居间服务", "交易所",
            "交易撮合", "数据市场", "挂牌上架"
        ],
        "description": "适用于中介方提供数据交易撮合服务的场景（甲方为委托方，乙方为中介方）",
        "parties": ["甲方（委托方）", "乙方（中介方）", "丙方（可选）", "丁方（可选）"],
        "articles": 11,
    },
}


def _normalize_text(text: str) -> str:
    """Normalize user text for robust keyword matching."""
    if not text:
        return ""
    text = text.lower().strip()
    # Remove most punctuation/whitespace to handle variants like "数据-委托 处理"
    return re.sub(r"[\s\-_，。！？、；：,.!?;:()（）【】\[\]\"'“”‘’]+", "", text)


def _extract_code_variants(text: str) -> set[str]:
    """Extract normalized code variants from text, e.g. GF-2025-2616 -> gf20252616."""
    if not text:
        return set()
    raw = text.lower()
    compact = re.sub(r"[^a-z0-9]+", "", raw)
    return {raw, compact}


def detect_contract_type_detailed(user_input: str) -> dict:
    """
    Detect contract type from user input using weighted matching.
    
    Args:
        user_input: Natural language description of user's intent
        
    Returns:
        {
            "type": Optional[str],
            "scores": dict[str, int],
            "ambiguous": bool,
        }
    """
    raw = user_input or ""
    normalized = _normalize_text(raw)
    
    # Score each type based on keyword matches
    scores = {}
    exact_hit = False
    raw_code_variants = _extract_code_variants(raw)
    for type_key, info in CONTRACT_TYPES.items():
        score = 0
        # Strong boost for exact contract name/code mention
        if info["name"] in raw or _normalize_text(info["name"]) in normalized:
            score += 100
            exact_hit = True
        code_variants = _extract_code_variants(info["code"])
        if raw_code_variants.intersection(code_variants):
            score += 120
            exact_hit = True
        if type_key in raw.lower():
            score += 80
            exact_hit = True

        for kw in info["keywords"]:
            kw_norm = _normalize_text(kw)
            if kw in raw or (kw_norm and kw_norm in normalized):
                # Longer keywords are usually more specific
                score += max(4, len(kw_norm))
        if score > 0:
            scores[type_key] = score

    if not scores:
        return {"type": None, "scores": {}, "ambiguous": False, "source": "rule"}

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_type, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else -1

    # Ambiguous if top two are too close and no strong exact hit.
    ambiguous = len(ranked) > 1 and (best_score - second_score) <= 3 and not exact_hit

    detected = None if ambiguous else best_type
    return {"type": detected, "scores": scores, "ambiguous": ambiguous, "source": "rule"}


def get_semantic_routing_prompt(user_input: str, top_k: int = 3) -> str:
    """
    Generate a structured prompt for the Skill's built-in model to do semantic routing.
    This does NOT call any external API; caller can feed this prompt to current model.
    """
    detail = detect_contract_type_detailed(user_input)
    ranked = sorted(detail.get("scores", {}).items(), key=lambda kv: kv[1], reverse=True)
    candidates = ranked[:top_k] if ranked else list(CONTRACT_TYPES.items())[:top_k]
    lines = [
        "请基于用户意图进行语义路由，返回合同类型编码（tigong/weituo/ronghe/zhongjie）之一。",
        "要求：优先选择语义最匹配的合同类型；若信息不足，先追问用户场景再决定。",
        "",
        f"用户输入：{user_input}",
        "",
        "候选类型：",
    ]
    for item in candidates:
        key = item[0]
        info = CONTRACT_TYPES[key]
        score = detail.get("scores", {}).get(key, 0)
        lines.append(f"- {key}: {info['name']}（{info['code']}），规则分={score}，说明：{info['description']}")
    lines.append("")
    lines.append("输出格式：仅输出编码（例如 weituo）。")
    return "\n".join(lines)

    
def detect_contract_type(user_input: str) -> Optional[str]:
    """Backward-compatible contract type detection API."""
    return detect_contract_type_detailed(user_input).get("type")


def get_contract_info(type_key: str) -> dict:
    """Get full info for a contract type."""
    return CONTRACT_TYPES.get(type_key)


def list_all_types() -> str:
    """Generate a formatted list of all supported contract types for display."""
    lines = ["📋 支持的合同类型：\n"]
    for i, (key, info) in enumerate(CONTRACT_TYPES.items(), 1):
        lines.append(f"  {i}. **{info['name']}**（{info['code']}）")
        lines.append(f"     {info['description']}")
        lines.append(f"     当事人：{' / '.join(info['parties'])}")
        lines.append("")
    return "\n".join(lines)


def get_disambiguation_prompt() -> str:
    """Generate a prompt asking user to clarify which contract type they need."""
    return f"""我无法确定您需要哪种合同类型。请告诉我您的具体场景：

{list_all_types()}

请描述您的数据交易场景，或直接告诉我需要哪种合同（如"数据提供合同"）。"""


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    test_inputs = [
        "帮我填一个数据提供合同",
        "GF-2025-2616",
        "我要把数据委托给别人处理",
        "多方一起开发数据产品，需要签融合合同",
        "我是数据交易平台，帮别人撮合交易",
        "我要签合同",
    ]
    for inp in test_inputs:
        detail = detect_contract_type_detailed(inp)
        t = detail["type"]
        name = CONTRACT_TYPES[t]["name"] if t else "Unknown"
        print(f"Input: {inp}")
        print(f"  -> {t} ({name})  scores={detail['scores']}  source={detail['source']}")
        print()
