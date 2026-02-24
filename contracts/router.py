# -*- coding: utf-8 -*-
"""
Contract type router - automatically detect which contract type user wants.
"""

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


def detect_contract_type(user_input: str) -> Optional[str]:
    """
    Detect contract type from user input using keyword matching.
    
    Args:
        user_input: Natural language description of user's intent
        
    Returns:
        Contract type key (e.g., "tigong", "weituo") or None if not detected
    """
    user_input_lower = user_input.lower()
    
    # Score each type based on keyword matches
    scores = {}
    for type_key, info in CONTRACT_TYPES.items():
        score = 0
        for kw in info["keywords"]:
            if kw in user_input_lower or kw in user_input:
                # Longer keywords get higher scores
                score += len(kw)
        if score > 0:
            scores[type_key] = score
    
    if not scores:
        return None
    
    # Return highest scoring type
    return max(scores.keys(), key=lambda k: scores[k])


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
    # Test
    test_inputs = [
        "帮我填一个数据提供合同",
        "我要把数据委托给别人处理",
        "多方一起开发数据产品，需要签融合合同",
        "我是数据交易平台，帮别人撮合交易",
        "我要签合同",  # Should return None
    ]
    for inp in test_inputs:
        result = detect_contract_type(inp)
        print(f"Input: {inp}")
        print(f"  -> Type: {result} ({CONTRACT_TYPES[result]['name'] if result else 'Unknown'})")
        print()
