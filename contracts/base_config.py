# -*- coding: utf-8 -*-
"""
Base configuration and shared utilities for all contract types.
"""

from pathlib import Path
import importlib
from typing import Any

# Base directory for contract configs
CONTRACTS_DIR = Path(__file__).parent

# Template file names (relative to each contract type's directory)
TEMPLATE_FILENAME = "template.docx"


def get_config(contract_type: str) -> dict:
    """
    Dynamically load configuration for a specific contract type.
    
    Args:
        contract_type: One of "tigong", "weituo", "ronghe", "zhongjie"
        
    Returns:
        Dictionary with keys: PLACEHOLDER_GROUPS, FIELD_ALIASES, TEMPLATE_PATH
    """
    try:
        module = importlib.import_module(f".{contract_type}.config", package="contracts")
    except ImportError as e:
        raise ValueError(f"Unknown contract type: {contract_type}") from e
    
    return {
        "PLACEHOLDER_GROUPS": getattr(module, "PLACEHOLDER_GROUPS", {}),
        "FIELD_ALIASES": getattr(module, "FIELD_ALIASES", {}),
        "TEMPLATE_PATH": CONTRACTS_DIR / contract_type / TEMPLATE_FILENAME,
        "CONTRACT_NAME": getattr(module, "CONTRACT_NAME", ""),
        "CONTRACT_CODE": getattr(module, "CONTRACT_CODE", ""),
    }


def get_template_path(contract_type: str) -> Path:
    """Get absolute path to template DOCX for a contract type."""
    return CONTRACTS_DIR / contract_type / TEMPLATE_FILENAME


def get_all_fields(placeholder_groups: dict) -> list[str]:
    """Get flat list of all placeholder field names from groups."""
    fields = []
    for group in placeholder_groups.values():
        fields.extend(group["fields"])
    return fields


def get_group_for_field(field_name: str, placeholder_groups: dict) -> str | None:
    """Find which group a field belongs to."""
    for group_name, group_info in placeholder_groups.items():
        if field_name in group_info["fields"]:
            return group_name
    return None


def apply_aliases(field_values: dict, field_aliases: dict) -> dict:
    """Apply field aliases to auto-fill related fields."""
    updated = dict(field_values)
    for source, targets in field_aliases.items():
        if source in updated and updated[source]:
            for target in targets:
                if target not in updated or not updated[target]:
                    updated[target] = updated[source]
    return updated


def get_progress(field_values: dict, placeholder_groups: dict) -> dict:
    """Get fill progress statistics."""
    all_fields = get_all_fields(placeholder_groups)
    total = len(all_fields)
    filled = sum(1 for f in all_fields if f in field_values and field_values[f])
    
    group_progress = {}
    for group_name, group_info in placeholder_groups.items():
        g_total = len(group_info["fields"])
        g_filled = sum(1 for f in group_info["fields"] if f in field_values and field_values[f])
        group_progress[group_name] = {
            "filled": g_filled,
            "total": g_total,
            "complete": g_filled == g_total,
        }
    
    return {
        "total": total,
        "filled": filled,
        "percentage": round(filled / total * 100, 1) if total > 0 else 0,
        "groups": group_progress,
    }


def get_next_unfilled_group(field_values: dict, placeholder_groups: dict) -> str | None:
    """Get the next priority group that has unfilled fields.
    
    所有字段都是必填的，没有可选字段。
    使用 is_field_filled 进行严格检查。
    """
    sorted_groups = sorted(
        placeholder_groups.items(),
        key=lambda x: x[1]["priority"]
    )
    for group_name, group_info in sorted_groups:
        # 使用 is_field_filled 严格检查每个字段
        has_unfilled = any(
            not is_field_filled(f, field_values)
            for f in group_info["fields"]
        )
        if has_unfilled:
            return group_name
    return None


def get_unfilled_fields(field_values: dict, placeholder_groups: dict, group_name: str = None) -> list[str]:
    """Get list of unfilled fields, optionally filtered by group.
    
    所有字段都是必填的。一个字段被认为是"已填写"当且仅当：
    - 文本字段：值存在且非空字符串（不能是 True/False）
    - 复选框字段（☐开头）：值必须明确表示选中或不选
    """
    if group_name:
        fields = placeholder_groups[group_name]["fields"]
    else:
        fields = get_all_fields(placeholder_groups)
    
    unfilled = []
    for f in fields:
        if not is_field_filled(f, field_values):
            unfilled.append(f)
    
    return unfilled


# 复选框有效值常量
CHECKBOX_CHECKED_VALUES = (True, "true", "True", "☑", "checked", "是", "选中", "yes", "Yes", "YES", "1")
CHECKBOX_UNCHECKED_VALUES = (False, "false", "False", "☐", "unchecked", "否", "不选", "no", "No", "NO", "0")
CHECKBOX_VALID_VALUES = CHECKBOX_CHECKED_VALUES + CHECKBOX_UNCHECKED_VALUES


def is_checkbox_checked(val) -> bool:
    """判断复选框值是否表示"选中"状态"""
    return val in CHECKBOX_CHECKED_VALUES


def is_field_filled(field_name: str, field_values: dict) -> bool:
    """Check if a specific field is properly filled.
    
    返回 True 如果字段已正确填写，False 如果未填写或值无效。
    """
    if field_name not in field_values:
        return False
    
    val = field_values[field_name]
    
    if field_name.startswith("☐"):
        # 复选框：必须是有效的选中/不选值
        if val in CHECKBOX_VALID_VALUES:
            return True
        # 非空字符串也算（会被视为选中）
        if isinstance(val, str) and val.strip():
            return True
        return False
    else:
        # 文本字段：必须非空，且不能是布尔值
        if val is True or val is False:
            return False  # 布尔值对文本字段无效
        return bool(val and str(val).strip())


# ============================================================================
# Chinese Uppercase Amount Conversion (shared by all contracts)
# ============================================================================

DIGITS = "零壹贰叁肆伍陆柒捌玖"
UNITS = ["", "拾", "佰", "仟"]
BIG_UNITS = ["", "万", "亿", "兆"]


def amount_to_chinese(amount_str: str) -> str:
    """
    Convert numeric amount to Chinese uppercase.
    
    Examples:
        "500000" -> "伍拾万元整"
        "123456.78" -> "壹拾贰万叁仟肆佰伍拾陆元柒角捌分"
    """
    # Clean input
    amount_str = amount_str.strip()
    amount_str = amount_str.replace(",", "").replace("，", "")
    amount_str = amount_str.replace("元", "").replace("整", "")
    
    # Handle Chinese unit suffixes
    multiplier = 1
    if amount_str.endswith("万"):
        amount_str = amount_str[:-1]
        multiplier = 10000
    elif amount_str.endswith("亿"):
        amount_str = amount_str[:-1]
        multiplier = 100000000
    
    try:
        amount = float(amount_str) * multiplier
    except ValueError:
        return amount_str  # Return as-is if cannot parse
    
    # Split integer and decimal
    amount = round(amount, 2)
    int_part = int(amount)
    dec_part = round((amount - int_part) * 100)
    
    jiao = int(dec_part / 10)
    fen = int(dec_part % 10)
    
    # Convert integer part
    if int_part == 0:
        result = "零"
    else:
        result = _int_to_chinese(int_part)
    
    result += "元"
    
    # Decimal part
    if jiao == 0 and fen == 0:
        result += "整"
    elif jiao == 0:
        result += f"零{DIGITS[fen]}分"
    elif fen == 0:
        result += f"{DIGITS[jiao]}角"
    else:
        result += f"{DIGITS[jiao]}角{DIGITS[fen]}分"
    
    return result


def _int_to_chinese(n: int) -> str:
    """Convert integer to Chinese uppercase."""
    if n == 0:
        return "零"
    
    s = str(n)
    length = len(s)
    result = ""
    zero_flag = False
    
    for i, digit in enumerate(s):
        d = int(digit)
        pos = length - 1 - i
        section = pos // 4
        pos_in_section = pos % 4
        
        if d == 0:
            zero_flag = True
            if pos_in_section == 0 and section > 0:
                result += BIG_UNITS[section]
                zero_flag = False
        else:
            if zero_flag:
                result += "零"
                zero_flag = False
            result += DIGITS[d] + UNITS[pos_in_section]
            if pos_in_section == 0 and section > 0:
                result += BIG_UNITS[section]
    
    return result
