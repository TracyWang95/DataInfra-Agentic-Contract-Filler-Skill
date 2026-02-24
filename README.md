# 国家数据局合同自动填写 Skill

多轮对话交互式填写国家数据局示范合同模板，自动路由识别合同类型，生成清洁版 `.docx` 合同文件。

## 支持的合同类型

| 编号 | 合同名称 | 编码 | 占位符数量 |
|------|---------|------|-----------|
| 1 | 数据提供合同 | GF-2025-2615 | 189 |
| 2 | 数据委托处理服务合同 | GF-2025-2616 | 137 |
| 3 | 数据融合开发合同 | GF-2025-2617 | 224 |
| 4 | 数据中介服务合同 | GF-2025-2618 | 156 |

## 核心特性

- ✅ **自动路由**：根据用户意图自动识别合同类型
- ✅ **多轮对话**：按分组优先级逐轮收集信息
- ✅ **智能推断**：自动转换金额大写、推断关联字段
- ✅ **别名联动**：填写一个字段自动填充相关字段
- ✅ **所有字段必填**：严格验证，确保合同完整
- ✅ **复选框支持**：正确处理 ☑/☐ 选择状态

## 快速开始

### 1. 安装依赖

```bash
pip install python-docx
```

### 2. 初始化合同

```bash
# 根据用户意图自动识别类型
python scripts/init_contract.py --intent "帮我填数据提供合同" --state "./contract_state.json"

# 或明确指定类型
python scripts/init_contract.py --type tigong --state "./contract_state.json"
```

类型参数：
- `tigong` - 数据提供合同
- `weituo` - 数据委托处理服务合同
- `ronghe` - 数据融合开发合同
- `zhongjie` - 数据中介服务合同

### 3. 更新字段

```bash
# 单个字段
python scripts/update_state.py --state "./contract_state.json" --field "甲方名称" --value "北京数据科技有限公司"

# 批量更新
python scripts/update_state.py --state "./contract_state.json" --json '{"甲方名称": "北京数据科技有限公司", "乙方名称": "上海智能技术有限公司"}'

# 查看进度
python scripts/update_state.py --state "./contract_state.json" --show
```

### 4. 生成合同

```bash
python scripts/fill_contract.py --state "./contract_state.json" --output "./合同_成品.docx"
```

## 目录结构

```
data-contract-skill/
├── README.md                   # 本文件
├── SKILL.md                    # AI Agent 使用说明
├── contracts/                  # 合同配置和模板
│   ├── base_config.py          # 共享配置和工具函数
│   ├── router.py               # 合同类型路由器
│   ├── tigong/                 # 数据提供合同
│   │   ├── config.py           # 占位符分组、别名配置
│   │   └── template.docx       # 模板文件
│   ├── weituo/                 # 数据委托处理服务合同
│   ├── ronghe/                 # 数据融合开发合同
│   └── zhongjie/               # 数据中介服务合同
├── scripts/
│   ├── init_contract.py        # 初始化合同状态
│   ├── update_state.py         # 更新字段值
│   └── fill_contract.py        # 生成最终合同
└── examples/
    └── sample_state.json       # 示例状态文件
```

## 必填规则

- **所有字段必填**：每个字段都必须填写，除非用户明确说"暂时不填"
- **复选框必填**：必须明确选中（☑）或不选（☐）
- **严格验证**：生成前检查所有字段，未填完无法生成

## 复选框处理

复选框字段以 `☐` 开头，支持以下值：

| 选中状态 | 不选状态 |
|---------|---------|
| `"☑"`, `"是"`, `"选中"`, `true` | `"☐"`, `"否"`, `"不选"`, `false` |

示例：
```json
{
  "☐甲方_统一社会信用代码": "☑",
  "☐甲方_居民身份证": "☐"
}
```

## 与 Claude Code 配合使用

1. 将此目录作为 skill 导入 Claude Code
2. Claude 会自动读取 SKILL.md 了解使用方法
3. 通过多轮对话收集用户信息并填写合同

## License

MIT
