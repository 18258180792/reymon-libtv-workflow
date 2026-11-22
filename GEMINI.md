# 工作区规则入口（Gemini CLI / Antigravity）

本项目的全部核心执行铁律、跨 Agent 环境自检指引与技能调用规范均统一维护在根目录 `AGENTS.md` 中。

- **单一事实源**：请先完整读取项目根目录的 `AGENTS.md` 并严格遵照执行。
- **开局自检**：首次在新机器运行前，可执行 `python3 scripts/setup.py --check` 确认技能、产品资产与蓝图校验就绪。
- **关键目录**：
  - 技能包：`.agents/skills/`（`reymon-ad-reverse-workflow`、`commercial-image-prompt-pro`、`cinematic-storyboard-director`）
  - SKU 与实拍图资产：`products/`（含内置 `products/reymon-cat-litter/` 标杆物料与 `products/_sku_template/`）
  - 跨 Agent 配置说明：`docs/AGENT_SETUP.md`
