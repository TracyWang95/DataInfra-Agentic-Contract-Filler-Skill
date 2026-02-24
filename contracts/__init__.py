# -*- coding: utf-8 -*-
"""
Data Contract Skill - Multi-contract template filling with auto-routing.

Supports 4 contract types from National Data Administration:
- GF-2025-2615: 数据提供合同
- GF-2025-2616: 数据委托处理服务合同
- GF-2025-2617: 数据融合开发合同
- GF-2025-2618: 数据中介服务合同
"""

from .router import (
    CONTRACT_TYPES,
    detect_contract_type,
    get_contract_info,
    list_all_types,
    get_disambiguation_prompt,
)

__all__ = [
    "CONTRACT_TYPES",
    "detect_contract_type",
    "get_contract_info",
    "list_all_types",
    "get_disambiguation_prompt",
]
