# 跨 Agent 接入与环境初始化指南（Multi-Agent Onboarding Guide）

本仓库采用 **单一事实源（`AGENTS.md` + `.agents/skills/` + `products/`）** 架构，已内置全部 3 个专业技能包与瑞梦迪标杆产品实拍素材，任何支持本地工作区的 AI 编程/创作 Agent 拉取仓库后均可开箱即用。

---

## 一、 一键让其他 Agent 自动初始化（可直接复制发送给新 Agent）

当你在另一台电脑或另一个 AI Agent（Claude Code / Cursor / Codex / Antigravity / Gemini CLI / OpenCode）中打开本仓库时，直接复制下面这段话发给它即可完成自检、技能挂载与环境验证：

```text
请先完整读取根目录 AGENTS.md，然后运行 `./setup.sh`（或 `python3 scripts/setup.py --check`）完成工作区自检与当前 Agent 技能挂载。若需要联网拉取参考视频或离线执行 CLI 建图，再运行 `./setup.sh --install-deps` 安装 yt-dlp 与 libtv CLI；建图时优先检查你的 LibTV MCP 是否就绪（`doctor`），且所有节点严格保持 `run=false` 零自动扣费。准备完毕后汇报自检结果并等待我发参考视频。
```

---

## 二、 主流 Agent 兼容性矩阵

| Agent / IDE | 自动加载的规则入口 | 技能包发现路径（`SKILL.md`） | 推荐初始化命令 |
| :--- | :--- | :--- | :--- |
| **Antigravity** | 原生自动加载 `AGENTS.md` / `GEMINI.md` | 原生发现 `.agents/skills/*` | `python3 scripts/setup.py --check` |
| **Claude Code** | 原生加载 `CLAUDE.md`（已通过 `@AGENTS.md` 导入全量规则） | 项目级 `.claude/skills/*` 或全局 `~/.claude/skills/*` | `./setup.sh`（或 `--agent claude --scope global`） |
| **Cursor** | 原生自动加载 `.cursor/rules/reymon-workflow.mdc`（`alwaysApply: true`） | 项目级 `.cursor/skills/*` 或 `.agents/skills/*` | `./setup.sh`（或 `--agent cursor --scope global`） |
| **OpenAI Codex CLI** | 原生自动加载根目录 `AGENTS.md` | 原生发现 `.agents/skills/*` | `python3 scripts/setup.py --check` |
| **Gemini CLI** | 原生自动加载 `GEMINI.md`（引导读取 `AGENTS.md`） | 原生发现 `.agents/skills/*` 或 `~/.agents/skills/*` | `python3 scripts/setup.py --check` |
| **OpenCode** | 原生自动加载 `AGENTS.md` | 原生发现 `.agents/skills/*` | `python3 scripts/setup.py --check` |
| **Windsurf / 其他 Agent** | 手动让 Agent 先读 `AGENTS.md` | 直接读取 `.agents/skills/*/SKILL.md` | `python3 scripts/setup.py --check` |

---

## 三、 技能安装与同步方式（项目级 vs 全局级）

仓库内的 `.agents/skills/` 包含以下 3 个完整技能（均含 `SKILL.md`、`references/` 词表规范与 `scripts/` 校验脚本）：
1. `reymon-ad-reverse-workflow` —— V3.0 双模式反推与 LibTV 无限画布编排主技能
2. `commercial-image-prompt-pro` —— 8 维商业摄影光学、四点布光与 PBR 微观材质静帧提示词技能
3. `cinematic-storyboard-director` —— V3.0 分镜调度、`4.0~4.2 字/秒` 恒定字速与单镜禁 BGM 视频提示词技能

### 方式 1：项目级初始化（推荐，安全无全局污染）
```bash
./setup.sh
```
默认等价于 `python3 scripts/setup.py --init-env --agent all --scope project --check`：
- 若不存在 `.env`，从 `.env.example` 复制生成 `.env`；
- 将 `.agents/skills/*` 通过软链接（若系统不支持自动回退复制）挂载到 `.claude/skills/` 与 `.cursor/skills/`（已被 `.gitignore` 忽略，不污染 Git）；
- 执行全量只读自检并校验 `runs/demo_reymon_sample/canvas_blueprint.json`。

### 方式 2：全局安装到指定 Agent 用户目录
如果你希望在其他项目里也能复用这 3 个技能：
```bash
# 安装到当前用户的 Claude Code 全局目录 (~/.claude/skills/)
python3 scripts/setup.py --agent claude --scope global

# 安装到当前用户的 Cursor / Codex / Antigravity / Gemini 全局目录
python3 scripts/setup.py --agent cursor --scope global
python3 scripts/setup.py --agent codex --scope global
python3 scripts/setup.py --agent antigravity --scope global
python3 scripts/setup.py --agent gemini --scope global
```
若后续团队使用 `skills` CLI（Node.js），也可直接执行 `npx skills add <你的GitHub用户名>/reymon-libtv-workflow`（将 `<你的GitHub用户名>` 替换为你的仓库 Owner）。

---

## 四、 LibTV 云端画布连接配置（双通路二选一）

### 通路 A：LibTV Remote MCP（主力推荐）
1. 在宿主 Agent（如 Antigravity、Claude Code、Cursor 等）中启用并登录官方 **LibTV Remote MCP** 服务；
2. 发起任务时，Agent 会自动先调用 `doctor` 探测登录态与连接权限，再通过 `create_project` / `target_project`、`create_node`（强制 `run=false`）在云端生成分组、标注卡、原生分镜表与 `480p Flash` 预连线画布。

### 通路 B：LibTV CLI 离线降级脚本（无 MCP 环境适用）
1. 安装可选 CLI 依赖（含 `libtv` CLI 与参考链接下载工具 `yt-dlp`）：
   ```bash
   ./setup.sh --install-deps
   ```
2. 完成鉴权登录（二选一）：
   - **网页扫码/OAuth 登录**：运行 `~/.libtv/libtv login web`；
   - **Access Key 环境变量**：在根目录 `.env` 中填入你的真实 `LIBTV_ACCESS_KEY`。
3. 核验连通性与当前账户可用生图/视频模型：
   ```bash
   bash .agents/skills/reymon-ad-reverse-workflow/scripts/check_env_and_libtv.sh
   ```

---

## 五、 预置产品资产与新 SKU 扩展

- **已随仓库内置的瑞梦迪标杆素材**（位于 `products/reymon-cat-litter/`）：
  - `product_brief.md`：瑞梦迪 5合1 植物膨润土混合猫砂（白茶款 2.5kg）视觉与成分防幻觉档案；
  - `assets/packshots/pack_front.png`：单袋正面高清实拍底图；
  - `assets/inner_granules/granules_macro.png`：五合一内料纯颗粒无字微距真图；
  - `assets/inner_granules/detail_5in1_formula.png` & `detail_granules_raw.png`：官方配比与颗粒原图。
- **新增自定义产品 / SKU**：
  - 无需预先手工搭建，直接参考 `products/_sku_template/product_brief_template.md` 或在对话中把新品卖点与实拍图发给 Agent，Agent 会自动沉淀到 `products/<sku_slug>/`。
