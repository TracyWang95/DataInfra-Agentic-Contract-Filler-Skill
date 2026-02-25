# -*- coding: utf-8 -*-
"""
Update contract state with new field values.

Usage:
    python update_state.py --state "state.json" --field "甲方名称" --value "北京数据科技有限公司"
    python update_state.py --state "state.json" --json '{"甲方名称": "北京数据科技有限公司", "乙方名称": "上海智能技术有限公司"}'
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))

from contracts.base_config import get_progress, get_next_unfilled_group, get_unfilled_fields, get_all_fields


def update_state(state_path: str, updates: dict) -> dict:
    """Update field values in the state file."""
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    field_values = state.get("field_values", {})
    field_values.update(updates)
    state["field_values"] = field_values
    
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    return state


def _normalize_field_name(name: str) -> str:
    """Normalize field name for fuzzy matching (ignore underscores/spaces/punct)."""
    if not isinstance(name, str):
        return ""
    name = name.strip().lower()
    return re.sub(r"[\s_\-（）()【】\[\]，。！？、；：,.!?;:]+", "", name)


def canonicalize_updates(updates: dict, valid_fields: list[str]) -> tuple[dict, list[str], dict]:
    """
    Map user-provided field names to canonical names in template/config.
    Returns:
      resolved_updates, unknown_fields, suggestions
    """
    normalized_map = {}
    for f in valid_fields:
        key = _normalize_field_name(f)
        normalized_map.setdefault(key, []).append(f)

    resolved = {}
    unknown = []
    suggestions = {}

    for raw_key, value in updates.items():
        # exact match first
        if raw_key in valid_fields:
            resolved[raw_key] = value
            continue

        norm = _normalize_field_name(raw_key)
        candidates = normalized_map.get(norm, [])
        if len(candidates) == 1:
            resolved[candidates[0]] = value
            continue
        if len(candidates) > 1:
            # ambiguous mapping, do not guess silently
            unknown.append(raw_key)
            suggestions[raw_key] = candidates[:5]
            continue

        # fallback fuzzy suggestions
        similar = difflib.get_close_matches(raw_key, valid_fields, n=5, cutoff=0.6)
        unknown.append(raw_key)
        if similar:
            suggestions[raw_key] = similar

    return resolved, unknown, suggestions


def main():
    parser = argparse.ArgumentParser(description="更新合同状态文件")
    parser.add_argument("--state", required=True, help="状态文件路径")
    parser.add_argument("--field", help="要更新的字段名")
    parser.add_argument("--value", help="字段值")
    parser.add_argument("--json", help="JSON格式的多个字段更新")
    parser.add_argument("--delete", nargs="+", metavar="FIELD", help="删除指定字段值（重置为未填写）")
    parser.add_argument("--show", action="store_true", help="显示当前状态")
    args = parser.parse_args()
    
    state_path = Path(args.state)
    if not state_path.exists():
        print(f"ERROR: 状态文件不存在：{state_path}")
        sys.exit(1)
    
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    if args.show:
        contract_name = state.get("contract_name", "合同")
        field_values = state.get("field_values", {})
        groups = state.get("groups", {})
        
        progress = get_progress(field_values, groups)
        print(f"📋 {contract_name} 填写进度：{progress['filled']}/{progress['total']}（{progress['percentage']}%）")
        print()
        
        for group_name in sorted(groups.keys(), key=lambda g: groups[g]["priority"]):
            gp = progress["groups"].get(group_name, {})
            status = "✅" if gp.get("complete") else "⬜"
            print(f"  {status} {group_name}：{gp.get('filled', 0)}/{gp.get('total', 0)}")
        
        # 显示未填写字段
        unfilled = get_unfilled_fields(field_values, groups)
        if unfilled:
            print(f"\n⚠️  仍有 {len(unfilled)} 个字段未填写：")
            for f in unfilled[:20]:
                marker = "☐" if f.startswith("☐") else "📝"
                print(f"   {marker} {f}")
            if len(unfilled) > 20:
                print(f"   ... 及其他 {len(unfilled) - 20} 项")
            
            # 提示下一个待填分组
            next_group = get_next_unfilled_group(field_values, groups)
            if next_group:
                print(f"\n📌 下一个待填分组：{next_group}")
                print(f"   提示：{groups[next_group].get('ask', '')}")
        else:
            print(f"\n🎉 所有字段已填写完成！可以生成合同。")
        return
    
    # Handle --delete
    if args.delete:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        field_values = state.get("field_values", {})
        deleted = []
        for field_name in args.delete:
            if field_name in field_values:
                del field_values[field_name]
                deleted.append(field_name)
        state["field_values"] = field_values
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        if deleted:
            print(f"✅ 已删除 {len(deleted)} 个字段值：{', '.join(deleted)}")
        else:
            print("⚠️  指定的字段不在已填写列表中，无需删除。")
        return

    updates = {}
    
    if args.field and args.value:
        updates[args.field] = args.value
    
    if args.json:
        try:
            json_updates = json.loads(args.json)
            updates.update(json_updates)
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON解析失败：{e}")
            sys.exit(1)
    
    if not updates:
        print("ERROR: 请提供 --field/--value 或 --json 参数")
        sys.exit(1)

    # Validate / canonicalize field names to avoid silent mismatch (e.g. 甲方证件号码 vs 甲方_证件号码)
    valid_fields = get_all_fields(state.get("groups", {}))
    resolved_updates, unknown_fields, suggestions = canonicalize_updates(updates, valid_fields)
    if unknown_fields:
        print("ERROR: 存在无法识别的字段名，已拒绝写入：")
        for f in unknown_fields:
            print(f"  - {f}")
            if f in suggestions:
                print(f"    可能是：{', '.join(suggestions[f])}")
        print("\n请使用 --show 查看标准字段名后重试。")
        sys.exit(1)
    updates = resolved_updates
    
    state = update_state(str(state_path), updates)
    
    field_values = state.get("field_values", {})
    groups = state.get("groups", {})
    progress = get_progress(field_values, groups)
    
    print(f"✅ 已更新 {len(updates)} 个字段")
    print(f"   当前进度：{progress['filled']}/{progress['total']}（{progress['percentage']}%）")
    
    # 显示剩余未填字段数量和下一步提示
    unfilled = get_unfilled_fields(field_values, groups)
    if unfilled:
        next_group = get_next_unfilled_group(field_values, groups)
        print(f"\n❌ 仍有 {len(unfilled)} 个字段【必须填写】")
        
        if next_group:
            group_unfilled = get_unfilled_fields(field_values, groups, next_group)
            print(f"\n📌 当前分组 [{next_group}] 还有 {len(group_unfilled)} 个字段未填：")
            for f in group_unfilled[:10]:
                marker = "☐" if f.startswith("☐") else "📝"
                print(f"   {marker} {f}")
            if len(group_unfilled) > 10:
                print(f"   ... 及其他 {len(group_unfilled) - 10} 项")
            print(f"\n💬 请继续询问用户：{groups[next_group].get('ask', '')}")
    else:
        print(f"\n🎉 所有 {progress['total']} 个字段已填写完成！可以运行 fill_contract.py 生成合同。")


if __name__ == "__main__":
    main()
