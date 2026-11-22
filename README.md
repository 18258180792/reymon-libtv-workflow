# 信息流爆款反推与 LibTV 无限画布 `480p` 预连线工作台（V3.0 多SKU · 双模式版）

本工程面向信息流投流团队（内置**瑞梦迪猫砂**标杆资产与 3 套专业 Agent 技能包，支持**任意产品与多 SKU 动态输入**），实现从 **「爆款视频反推 → 双模式分镜与资产规划 → 导演级音画提示词 → LibTV 云端画布 `480p Flash` 预连线（零自动扣费）」** 的标准化投流生产流。

---

## 1. 快速开始（任意电脑 / 任意 AI Agent 开箱即用）

### 1.1 一键自检与初始化
```bash
git clone <你的仓库地址> reymon-libtv-workflow
cd reymon-libtv-workflow

# 项目级初始化：生成 .env（如缺失）、挂载技能软链接，并运行只读全套体检（零网络/零扣费）
./setup.sh

# （可选）若宿主 Agent 未接入 LibTV MCP，或需要下载短视频 URL，安装 libtv CLI 与 yt-dlp：
./setup.sh --install-deps
```

### 1.2 一键让其他 Agent 自动跑通（复制发给新 Agent）
> 请先完整读取根目录 `AGENTS.md`，然后运行 `./setup.sh`（或 `python3 scripts/setup.py --check`）完成工作区自检与技能挂载。若需离线建图或下载参考视频链接再运行 `./setup.sh --install-deps`；云端建图优先用 LibTV MCP（`doctor`），所有节点严格保持 `run=false` 零自动扣费。

### 1.3 跨 Agent 兼容性速览
| Agent / 工具 | 自动规则入口 | 技能挂载方式 | 详细说明 |
| :--- | :--- | :--- | :--- |
| **Antigravity / Codex / OpenCode / Gemini CLI** | `AGENTS.md` / `GEMINI.md` | 原生自动读取 `.agents/skills/*` | [docs/AGENT_SETUP.md](./docs/AGENT_SETUP.md) |
| **Claude Code** | `CLAUDE.md`（自动引入 `AGENTS.md`） | `./setup.sh` 自动挂载 `.claude/skills/*` | [docs/AGENT_SETUP.md](./docs/AGENT_SETUP.md) |
| **Cursor** | `.cursor/rules/reymon-workflow.mdc` | `./setup.sh` 自动挂载 `.cursor/skills/*` | [docs/AGENT_SETUP.md](./docs/AGENT_SETUP.md) |

---

## 2. 内置技能包与标杆物料清单

- **三大专业技能（`.agents/skills/`）**：
  - [reymon-ad-reverse-workflow](./.agents/skills/reymon-ad-reverse-workflow/SKILL.md)：V3.0 双模式反推编排、蓝图校验与 LibTV 画布预连线
  - [commercial-image-prompt-pro](./.agents/skills/commercial-image-prompt-pro/SKILL.md)：八维光学摄影、四点布光、PBR 微观材质与 `9:16` 全向安全区提示词专家
  - [cinematic-storyboard-director](./.agents/skills/cinematic-storyboard-director/SKILL.md)：分镜调度、`4.0~4.2 字/秒` 恒定语速锁、单镜禁 BGM 与模式 B 钩子切出衔接点
- **内置标杆产品资产（`products/`）**：
  - [products/reymon-cat-litter/product_brief.md](./products/reymon-cat-litter/product_brief.md)（瑞梦迪 5合1 白茶款 2.5kg 档案，已随仓携带 4 张实拍包装与纯颗粒微距 PNG 底图）
  - 新增其他猫砂或新品类 SKU：参考 [products/README.md](./products/README.md) 与模板 [product_brief_template.md](./products/_sku_template/product_brief_template.md)，或在对话时直接把新 SKU 信息发给 AI 自动创建。
- **离线验证模板（`runs/demo_reymon_sample/`）**：
  - 提供完整 `canvas_blueprint.json` 与可执行校验样本，供 `setup.py --check` 与离线 CLI 流程验证。

---

## 3. 核心特性：支持「双制作模式」与「多钩子赛马」

每次任务开始前，工作流会先与你快速对齐 **4 个核心选项**：
1. **本次产品 / SKU**：直接选用 `products/` 下已有档案，或在对话中随手发新产品/新 SKU 卖点与实拍图（自动建档沉淀）。
2. **制作模式（二选一）**：
   - **模式 A：【全 AI 统合全片模式】**
     - 适用场景：整条片子从头到尾纯 AI 出片。
     - 核心保障：**画面（Base Style + 三视图 + 实拍包装/内料真图锁）+ 音色与语速（同一 `Minimax` `voiceId` + 固定 `speed` + `4.0~4.2字/秒` 字速卡尺）+ 全局 BGM（单镜强制禁配乐 No BGM + 左侧独立生成 1 条 `ElevenMusic V3` 全局纯器乐 BGM）100% 统一**。
   - **模式 B：【轻量 AI 钩子 + 实拍混剪模式】**
     - 适用场景：前 3~6 秒用 AI 低成本做高吸睛戏剧/痛点钩子，中后段直接剪入你手机实拍的产品/内料硬核测试镜头。
     - 核心保障：画布**极简轻量，只搭建前 1~2 镜钩子节点**（绝不冗余搭建后段内料节点），并提供精准的**实拍切入点（Match Cut）建议**及可选的**同音色同语速后段实拍旁白 TTS 音频节点**，确保 AI 钩子切入实拍画面时声音不断层。
3. **投流裂变策略**：支持 **单条复刻精做**，也支持 **多钩子赛马裂变**（同一画布并行铺设 `Hook A / Hook B / Hook C` 多个前 3 秒钩子变体测跑消耗）。
4. **默认 `480p` 抽卡档位**：所有预连线视频节点默认预设 `Seedance 2.5 Flash` + `480p`（`run=false` 零自动扣费），进画布直接点跑测卡，无需手动逐个改分辨率。

---

## 4. 首次使用准备

1. **打开项目工作区并自检**
   在你的 AI IDE / 终端中打开本仓库目录，运行 `./setup.sh`（或让 Agent 执行 `python3 scripts/setup.py --check`）。
2. **确认 LibTV 连接就绪**（内置优先走云端 **LibTV MCP** 直连；无 MCP 环境可使用 `libtv` CLI 降级脚本，详见 [docs/AGENT_SETUP.md](./docs/AGENT_SETUP.md)）。
3. **确认产品 SKU 档案**：默认启用 `products/reymon-cat-litter/`，也可随时在对话中喂入全新 SKU 卖点与实拍图。

---

## 5. 日常如何跑一条任务？

直接在对话框输入参考视频（本地路径或链接），例如：
> “参考这个视频 `/路径/xxx.mp4`，帮我反推一套脚本。”

AI 会按以下节奏与你配合：
1. **第 0 步（开局 4 问对齐）**：快速确认本次推哪个 **产品/SKU**、走 **模式 A（全 AI）还是模式 B（轻量钩子+实拍）**、**单钩子还是多钩子赛马**、以及**核心卖点**。
2. **第 1 棒（拆片 + 定制剧本 + 需补素材清单）**：原生读取参考视频，输出 `01_reference_breakdown.md` 与 `02_script_and_asset_checklist.md`，停下来与你审改定稿。
3. **第 2 棒（全套提示词 + LibTV 画布 `480p` 预连线交付）**：剧本确认后，输出完整提示词总表并自动在云端画布铺好分组、标注卡、原生分镜表与 `480p` 视频预连线（严格 `run=false` 不自动扣费）。

---

## 6. 进入 LibTV 网页画布后的「零翻车 4 步点跑顺序」（必看！）

> **关键防坑提醒**：切勿在左侧音频/定妆底座还没生成出来前就直接点最右侧的视频节点！否则视频节点拿到的是空音频 URL，会导致模型随机捏音色！

打开交付的画布链接后，严格从左往右按顺序点击：
1. **第 1 步（先跑声音与视觉底座）**：
   - 检查 `01_包装` / `02_内料` 真图是否就绪（如需换实拍图先替换）；
   - **优先点击运行 `05_音色与全局BGM组` 里的 `Minimax` 音频节点（及模式 A 的全局 BGM 节点）**，确保生成出真实 `.mp3` 音频；
   - 点击运行 `03_环境道具` 与 `04_角色三视图` 静帧节点。
2. **第 2 步（跑分镜首尾静帧）**：
   - 点击生成右侧每行的分镜首帧（及尾帧）合成图，核对包装文字锐利无乱码、内料形态无变形、右侧 12% 与上下 18% 安全区无遮挡。
3. **第 3 步（`480p Flash` 低成本抽卡）**：
   - 静帧与左侧音色均就绪后，点击最右侧 `Seedance 2.5 Flash (480p)` 视频节点低成本抽卡（若之前重跑过上游素材导致节点提示过期，先确认引用已刷新再点运行）。
4. **第 4 步（成片统合）**：
   - **模式 A**：挑出每镜满意的卡片（可按需升级高清），在时间线或剪映中拼接各镜（单镜已禁自带 BGM），底部统一铺上左侧生成的**全局唯一 BGM 音轨（压底 `-15dB`）**与独立旁白干声；
   - **模式 B**：导出抽中的前 3~6 秒钩子视频（及同音色后段旁白音频），直接与你的手机实拍产品/内料镜头无缝混剪出片！
