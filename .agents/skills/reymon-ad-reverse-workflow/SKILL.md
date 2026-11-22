---
name: reymon-ad-reverse-workflow
description: >-
  Reverse-engineers reference short-form/feed ad videos into multi-SKU product scripts
  (with built-in Reymon/瑞梦迪 cat litter presets and dynamic custom SKU intake), supporting
  Dual Production Modes: Mode A (Full-AI Unified: 100% unified visuals, locked TTS voice/speed,
  single global BGM, No per-shot BGM) and Mode B (Lightweight AI Hook + Real-Shoot Hybrid),
  plus single-hook or multi-hook A/B testing on pre-wired 480p LibTV Infinite Canvas (run=false).
---

# 多产品多SKU · 双模式信息流视频反推与 LibTV `480p` 画布预连线工作流（V3.2）

本技能将任意爆款参考视频（或链接）转化为适配目标产品/SKU 的投流分镜方案，并支持 **「模式 A：全 AI 统合全片」** 与 **「模式 B：轻量 AI 钩子 + 实拍混剪」** 双轨交付，自动在 LibTV 云端画布完成分组、标注与 `Seedance 2.5 Flash (480p)` 预连线（**严格 `run=false` 零自动扣费**）。

## 执行前必读参考文档与联动子技能

- **【必调生图专家技能】**：[commercial-image-prompt-pro](../commercial-image-prompt-pro/SKILL.md)（V3.2：全局视觉风格锁、满画幅无边框安全构图、四模态分流、八维商业摄影光学、物理接触与实体预算）
- **【必调分镜导演技能】**：[cinematic-storyboard-director](../cinematic-storyboard-director/SKILL.md)（V3.2 双模式终版：全局视觉风格锁、满画幅无边框、Seedance 2.5 防崩坏四铁律、`4.0~4.2字/秒` 恒定字速、单镜禁 BGM + 分秒 Foley SFX）
- **【必用钩子矩阵与质检卡】**：[hook_matrix_and_eval_rubric.md](./references/hook_matrix_and_eval_rubric.md)（10 类钩子分类学、证据帧拆解字段、跨切角赛马矩阵、Gate 1 前置 3 视角 × 8 维度自检评分卡）
- **【必遵交付排版规范】**：[delivery_markdown_standard.md](./references/delivery_markdown_standard.md)（双模式剧本头 + 镜号四字标题 + 画布标注大小标题 + 防空 URL 分级点跑操作卡）
- **【双模式路由与防幻觉手册】**：[reymon_cat_litter_playbook.md](./references/reymon_cat_litter_playbook.md)
- **【画布分区拓扑规范】**：[canvas_blueprint_schema.md](./references/canvas_blueprint_schema.md)
- **【多产品/多 SKU 档案库】**：`products/`（参见 `products/README.md` 与模板 `products/_sku_template/product_brief_template.md`）

---

## 标准六步执行流程

### 阶段 0：开局 4 问需求对齐（Intake Gate · 任务启动必做）
收到参考视频或反推指令后，若用户未在首句交代完整，必须先用 `ask_question` 工具或精炼列表向用户确认以下 **4 个核心维度**：
1. **【产品与 SKU】**：使用已有档案（如 `products/reymon-cat-litter` 瑞梦迪 5合1 白茶款），还是本次新输入其他产品/SKU？（若用户在对话中提供了新 SKU 信息与实拍图，立即按 `products/_sku_template/product_brief_template.md` 在 `products/<sku_slug>/` 下建档归集）。
2. **【制作模式（二选一）】**：
   - **模式 A：全 AI 统合全片模式** —— 全片纯 AI 生成，强制锁死「全局画风 + 同源 TTS 音色与恒定语速 + 左侧独立 1 条全局纯器乐 BGM（单镜严禁生成 BGM）」；
   - **模式 B：轻量 AI 钩子 + 实拍混剪模式** —— 画布**仅轻量搭建前 1~2 镜（3~6s）吸睛钩子分镜**，后半段直接留给用户剪入手机实拍产品/内料镜头（同时询问是否需要顺手建 1 个同音色同语速的后段实拍旁白 TTS 音频节点）。
3. **【投流裂变策略】**：**单条复刻精做（1 套钩子）** 还是 **多钩子赛马测试（并行设计 2~3 个不同前 3 秒钩子变体 Hook A / Hook B / Hook C）**？
4. **【核心卖点与促销钩子】**：本次重点打哪 1~2 个痛点或转化机制？

---

### 阶段 1：创建批次目录与原生多模态音画拆解
1. 在 `runs/` 下创建当前批次目录：`runs/YYYYMMDD_<SKU简称>_<参考片简称>/`（内设 `input/` 子目录）。
2. **获取并读取参考视频**：
   - 本地视频文件：直接调用 `read_file` 原生读取画面切镜、景别运镜、口播字速与音效卡点；
   - 视频 URL：运行 [fetch_reference_video.py](./scripts/fetch_reference_video.py) 下载至 `input/` 后读取；若遇平台登录墙限制，提示用户将无水印 MP4 放入 `input/`。
3. 输出 `01_reference_breakdown.md`：包含**逐秒切镜拆解表**与**爆款转化骨架提炼**（对照 [hook_matrix_and_eval_rubric.md](./references/hook_matrix_and_eval_rubric.md) 明确**钩子类型定性 H01–H10**、并必填 **`证据帧时间戳`**、**`镜头物理动势与切镜节拍`** 与 **`静音前 2 秒可读性`**，提取前 3 秒留人机制、情绪反转点、产品切入秒数与逼单 CTA）。

---

### 阶段 2：按所选模式编写定制剧本与《素材/实拍对接清单》
读取目标 SKU 的 `product_brief.md` 并扫描其 `assets/` 目录，编写 `02_script_and_asset_checklist.md`：
- **多钩子赛马硬约束**：若选赛马测试，强制依据 [hook_matrix_and_eval_rubric.md](./references/hook_matrix_and_eval_rubric.md) 跨**心理切角 × 钩子类型**设计 `Hook A / B / C`（严禁只改词序同质化），并为每条变体标注**假设驱动测试指标**（测 3s 留存 / CTR / CVR）；
- **若为【模式 A：全 AI 统合全片模式】**：
  - 编写完整逐镜视觉脚本（含多钩子变体，如选赛马策略），严格执行 **`4.0~4.2 汉字/秒` 字速卡尺**（杜绝同为 5s 视频因字数悬殊导致倍速或拖腔）；
  - 严格执行产品/内料镜 **1 镜 1 节点拆解**（倒砂/结团铲底等状态跳变镜配置**首尾帧双静帧锁**）；
  - 盘点《需上传真图 / 画布 AI 底座 / 音色与全局唯一 BGM 配置表》。
- **若为【模式 B：轻量 AI 钩子 + 实拍混剪模式】**：
  - **重度精雕前 1~2 镜（0~6s）AI 钩子分镜**（若选赛马策略，则横向列出 `Hook A / Hook B / Hook C` 多套钩子方案）；
  - **轻量化列出后半段【实拍混剪对接表】**：不写冗余的后段 AI 生图生视频节点，而是清晰写明 **「第 X.Xs 钩子切出画面与动作落点（Match Cut） → 建议接入哪几段手机实拍镜头（景别/时长/动作） → 贯穿全片的同音色旁白台词卡点」**。

---

### 阶段 3：前置质检与人机对话审改定稿（停顿门禁 Gate 1）
1. **Gate 1 前置自检**：交付用户审稿前，先按 [hook_matrix_and_eval_rubric.md](./references/hook_matrix_and_eval_rubric.md) 执行 **「3 专家视角 × 8 维度自检评分卡」**（重点核验**静音前 2 秒可读性**与 **`4.0~4.2字/秒` 字速合规**）；任一维度 `< 7` 分（或字速不达标）先自动修补一轮，再将简版评分与修订亮点附于 `02_script_and_asset_checklist.md` 末尾。
2. 向用户展示 `01_reference_breakdown.md` 结论与 `02_script_and_asset_checklist.md`，**主动暂停并确认**：
   - 钩子冲突感、台词字数与节奏、卖点侧重与评分卡结论是否满意？
   - 所需的新 SKU 包装图/内料真图是否已就位？确认无误后再进入画布搭建。

---

### 阶段 4 & 5：输出提示词总表并推送至 LibTV `480p` 预连线画布（零自动扣费）
1. 输出终版导演脚本与全量提示词文档 `04_director_visual_script_final.md`（遵循 [delivery_markdown_standard.md](./references/delivery_markdown_standard.md)）：必须先在文首固化全片唯一的 **【全局视觉风格锁】**（成片镜统一全局电影质感与色彩科学）与 **【上游棚拍底座质感子句】**（中性 5500K 棚拍防串色），并逐字嵌入对应所有静帧与视频 Prompt；**严禁在生图/生视频 Prompt 中直写 `18% / 12% / 安全区 / 避让区` 等 UI 排版词汇（统一转译为满画幅实景自然延展与主体偏左三分线构图）**。
2. 优先通过 **LibTV MCP**（`doctor` → `create_project` / `target_project` → `search_models` / `get_model`）搭建云端无限画布（所有节点强制 `run=false`）：
   - **默认模型档位**：静帧绑定 `Lib Image 2.6 Pro`（`lib-image-2.6-s`）；**所有视频节点默认绑定 `Seedance 2.5 Flash`（`star-video2.5-flash`）+ `resolution="480p"` + `ratio="9:16"`**；TTS 绑定 `Minimax-speech-2.8-hd`（`speech-2.8-hd`，同一角色锁死同一 `voiceId` 与 `voice_setting_speed`）；模式 A 全局配乐绑定 `ElevenMusic V3`（`vocal-music`，`instrumental=1`，`duration=30000`）。
   - **提示词引用语法**：MCP 节点提示词统一使用精确的 **`{{Node <nodeId>}}`** 引用上游节点（由服务端自动映射序号，严禁人工手算 Mixed 序号）。
   - **按模式精准建图（绝不多建废节点）**：
     - **模式 A（全 AI 全片）**：建 `00A_官方 Script V2 分镜表` + `00_总剧本与分级点跑指南` + 左侧 5 大分类素材组（`01包装` / `02内料` / `03环境道具` / `04角色三视图` / `05角色音色锁与全局唯一BGM组`，每节点正上方 `Y-260` 配 `📌` 标注卡）+ 右侧全片逐行分镜组。
     - **模式 B（轻量钩子 + 实拍混剪）**：仅建 `00_钩子剧本与实拍混剪指南` + 钩子必需的 `角色/环境/音色组`（可选含 1 个同音色后段实拍旁白 TTS 节点）+ 右侧 **1~N 行钩子分镜组（Hook A / Hook B...）**，干净轻量！
3. 输出 `03_live_canvas_index.md`（记录精确 `projectId`、网页直达链接、分组与节点 ID 索引表），并醒目提醒用户严格按 **「第 1 步先跑左侧 05 音色/BGM 与 03/04 底座（防空 URL） → 第 2 步跑首尾静帧 → 第 3 步跑右侧 480p 视频抽卡」** 的顺序点击！
   - *(离线无 MCP 降级方案：生成 `canvas_blueprint.json` 并运行 [build_libtv_canvas.py](./scripts/build_libtv_canvas.py) 输出可审计 CLI 脚本)*。
